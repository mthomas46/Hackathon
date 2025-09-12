# Secure Analyzer

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/secure_analyzer](../../tests/unit/secure_analyzer)

## Key Features
- Sensitive content detection with configurable keyword sources.
- Policy-aware provider recommendations for summarization.
- Integrates with summarizer-hub via `ServiceClients`.
- Standard middlewares, `/health`, and consistent error handling.

Detects sensitive content (PII, secrets, proprietary info), suggests appropriate LLM providers, and enforces policy when summarizing.

## Endpoints
- `GET /health`
- `POST /detect` — `{ content, keywords?, keyword_document? }` → `{ sensitive, matches, topics }`
- `POST /suggest` — `{ content, keywords?, keyword_document? }` → `{ sensitive, allowed_models, suggestion }`
- `POST /summarize` — `{ content, providers?, override_policy?, keywords?, keyword_document?, prompt? }` → forwards to summarizer-hub ensuring policy

## Policy
- If sensitive: restrict to `bedrock` and `ollama` by default (`SECURE_ONLY_MODELS` env). Unless `override_policy=true`.
- If not sensitive: allow all providers (configurable via `ALL_PROVIDERS`).

## Config
- `SUMMARIZER_HUB_URL` (default `http://summarizer-hub:5060`)
- `SECURE_ONLY_MODELS` (default `bedrock,ollama`)
- `ALL_PROVIDERS` (default `bedrock,ollama,openai,anthropic,grok`)

## Environment
| Name | Description | Default |
|------|-------------|---------|
| SUMMARIZER_HUB_URL | Summarizer Hub URL | http://summarizer-hub:5060 |
| SECURE_ONLY_MODELS | Allowed models when sensitive | bedrock,ollama |
| ALL_PROVIDERS | All providers when not sensitive | bedrock,ollama,openai,anthropic,grok |
- `SUMMARIZER_HUB_URL` (default `http://summarizer-hub:5060`)
- `SECURE_ONLY_MODELS` (default `bedrock,ollama`)
- `ALL_PROVIDERS` (default `bedrock,ollama,openai,anthropic,grok`)
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.

## Keyword sources
- Inline `keywords: ["secret", "internal"]`
- `keyword_document`: URL pointing to newline/comma/semicolon-separated keywords

## Example
```
POST /suggest
{
  "content": "This includes an API key and client name."
}
→ { "sensitive": true, "allowed_models": ["bedrock","ollama"], "suggestion": "Sensitive content detected..." }
```

## Related
- Summarizer Hub: [../summarizer-hub/README.md](../summarizer-hub/README.md)

## Testing
- Unit tests: [tests/unit/secure_analyzer](../../tests/unit/secure_analyzer)
- Strategies:
  - Ensure policy enforcement reflected in provider list and summary responses
  - Include `analysis` field in summarize mock for compatibility
