# Summarizer Hub

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/summarizer_hub](../../tests/unit/summarizer_hub)

## Key Features
- **Ensemble Summarization**: Multi-provider summarization across Ollama, Bedrock, OpenAI, Anthropic, etc.
- **Automated Categorization**: ML-based document classification using zero-shot and traditional approaches
- **Batch Processing**: Efficient processing of multiple documents with categorization
- **Rate-limit Middleware**: Configurable rate limiting (toggle via `RATE_LIMIT_ENABLED`)
- **Config-driven Provider Selection**: Flexible provider configuration and timeouts
- **Standardized Middleware**: Health checks, metrics, and error handling

## Goal
- Provide comprehensive document processing capabilities including summarization and categorization
- Support multiple AI providers with ensemble analysis for consistency validation
- Enable automated document organization through ML-based classification
- Shield the ecosystem from provider-specific SDKs and credentials via unified configuration

## Overview and role in the ecosystem
- **Central Processing Hub**: Unified service for document summarization and categorization
- **Multi-Provider Support**: Ensemble analysis across heterogeneous AI providers
- **Automated Organization**: ML-based document classification and tagging for better discoverability
- **Quality Assurance**: Consistency analysis and categorization confidence scoring
- **Integration Ready**: Seamless integration with Doc Store, Analysis Service, and other ecosystem components

## Endpoints

### Core Endpoints
| Method | Path               | Description |
|--------|--------------------|-------------|
| GET    | /health            | Service health and capabilities check |
| POST   | /summarize         | Single document summarization |

### Categorization Endpoints
| Method | Path               | Description |
|--------|--------------------|-------------|
| POST   | /categorize        | Categorize single document with ML classification |
| POST   | /categorize/batch  | Batch categorize multiple documents |
| GET    | /categorize/categories | Get available document categories |

### Legacy Endpoints
| Method | Path               | Description |
|--------|--------------------|-------------|
| POST   | /summarize/ensemble | Ensemble summarization (deprecated) |

## Configuration
Config-first via `services/shared/config.get_config_value` with env override; optional `services/summarizer-hub/config.yaml` for provider defaults.

Environment:
- `RATE_LIMIT_ENABLED`
- `OLLAMA_HOST`
- `BEDROCK_MODEL`, `BEDROCK_REGION`, `BEDROCK_ENDPOINT`, `BEDROCK_API_KEY`
- `SH_CONFIG` (path to hub config yaml)

## Providers
- `ollama`: requires `endpoint` (e.g., http://ollama:11434) and `model`.
- `openai`/`anthropic`/`grok`: placeholders (wire real SDKs as needed).
- `bedrock`: set `endpoint` to a Bedrock proxy/gateway or configure `BEDROCK_ENDPOINT`; supports `model`, `region`, `api_key`.
  
## Integration
- Emits structured logs to `log-collector` when `LOG_COLLECTOR_URL` is set.

## Related
- Secure Analyzer: [../secure-analyzer/README.md](../secure-analyzer/README.md)

## Testing
- Unit tests: [tests/unit/summarizer_hub](../../tests/unit/summarizer_hub)
- Strategies:
  - Provider fan-out and ensemble shape assertions

### AWS SDK (native) usage
- Install dependencies (already in requirements.txt): `boto3`, `botocore`.
- Provide credentials via environment (preferred) or through standard AWS mechanisms:
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (optional), `AWS_REGION`.
- Request example (using config defaults):
```json
{
  "text": "Summarize this design...",
  "prompt": "Key decisions and risks.",
  "providers": [{"name": "bedrock"}],
  "use_hub_config": true
}
```
- The hub will invoke Bedrock via the native SDK; if SDK invocation fails or isn’t configured, it will try `BEDROCK_ENDPOINT` proxy.

### YAML configuration
- `services/summarizer-hub/config.yaml` supports provider defaults and AWS credentials:
```yaml
providers:
  - name: bedrock
    model: ${BEDROCK_MODEL:-anthropic.claude-3-sonnet-20240229-v1:0}
    endpoint: ${BEDROCK_ENDPOINT:-}
    region: ${BEDROCK_REGION:-us-east-1}
    api_key: ${BEDROCK_API_KEY:-}
aws:
  access_key_id: ${AWS_ACCESS_KEY_ID:-}
  secret_access_key: ${AWS_SECRET_ACCESS_KEY:-}
  session_token: ${AWS_SESSION_TOKEN:-}
  region: ${AWS_REGION:-us-east-1}
```

### Using the local Bedrock proxy stub (for demos)
- Start the proxy: `uvicorn services.bedrock-proxy.main:app --host 0.0.0.0 --port 7090`
- Set `BEDROCK_ENDPOINT=http://localhost:7090/invoke`
- Call summarizer-hub with a `bedrock` provider as usual. The hub will send your prompt to the proxy and return a canned/templated response.
- Note: the hub does not set proxy-specific `template` fields. To use templates (e.g., `summary`, `pr_confidence`, `life_of_ticket`) for local demos, call the proxy directly:

```
POST http://localhost:7090/invoke
{
  "prompt": "Summarize: feature adds GET /hello with tests and docs",
  "template": "summary",
  "format": "md",
  "title": "Feature Summary"
}
```

## Future
- Implement real provider clients with secrets from env.
- Configurable voting/weighting and semantic comparison.
- Emit memory events and store results in memory-agent.

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.
