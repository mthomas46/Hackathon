# Bedrock Proxy Stub

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/bedrock_proxy](../../tests/unit/bedrock_proxy)

## Key Features
- Local stub for Bedrock requests with canned summarization responses.
- Useful for tests/demos when AWS integration is unavailable.
- Standard request logging and health endpoints.

A minimal local HTTP stub that emulates Amazon Bedrock responses for development without AWS credentials.

## Overview and role in the ecosystem
- Provides a safe, offline-compatible target for the Summarizer Hub when Bedrock credentials or network are unavailable.
- Accelerates local development and CI by returning deterministic, template-driven outputs.
- Allows teams to validate summary formats (md/txt/json) and downstream integrations without incurring provider costs.

## Endpoints
| Method | Path   | Description |
|--------|--------|-------------|
| GET    | /health| Liveness |
| POST   | /invoke| Accepts `{ model?, region?, prompt, params?, template?, style?, format?, title? }` |
  - `template`: `summary|risks|decisions|pr_confidence|life_of_ticket`
  - `style`: currently reserved for future (defaults to bullet style)
  - `format`: `md|txt|json` (defaults to `md`)
  - Returns:
    - for `md|txt`: `{ output, model, region }`
    - for `json`: `{ title, model, region, sections: {Heading: [items]} }`

## Usage
- Install deps: `pip install -r services/bedrock-proxy/requirements.txt`
- Run: `uvicorn services.bedrock-proxy.main:app --host 0.0.0.0 --port 7090`
- Configure summarizer-hub to use the proxy:
  - Set `BEDROCK_ENDPOINT=http://localhost:7090/invoke`
  - Or in YAML `services/summarizer-hub/config.yaml` under providers.bedrock.endpoint

### Example requests

Summary template (markdown):

```
POST /invoke
{
  "prompt": "Summarize: feature adds GET /hello with tests and docs",
  "template": "summary",
  "format": "md",
  "title": "Feature Summary"
}
```

PR Confidence template (json):

```
POST /invoke
{
  "prompt": "PR #42 implements /hello per HELLO-2",
  "template": "pr_confidence",
  "format": "json"
}
```

## Notes
- This is a stub; it returns the prompt prefixed with `[bedrock-proxy]`.
- For native AWS SDK testing, ensure proxy endpoint is unset and AWS credentials are provided instead.
 - Templates are for local development; summarizer-hub calls the proxy with `prompt` only and does not pass `template`.

## Shared utilities
- Uses middleware from `services/shared/request_id.py` and `services/shared/metrics.py`.
- See `services/shared/config.py` (YAML loader) and `services/shared/constants.py` (env keys).

## Related
- Summarizer Hub: [../summarizer-hub/README.md](../summarizer-hub/README.md)

## Testing
- Unit tests: [tests/unit/bedrock_proxy](../../tests/unit/bedrock_proxy)
- Strategies:
  - Template- and format-driven response shape checks
