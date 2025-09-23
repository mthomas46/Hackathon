# E2E Demo: Secure Summarization via Orchestrator

This walkthrough shows how to use the orchestrator to suggest appropriate LLM models based on sensitivity and execute a policy-aware summarization using `secure-analyzer` and `summarizer-hub`.

## Prerequisites
- Services running: orchestrator, secure-analyzer, summarizer-hub (and optional bedrock-proxy for dev)
- Environment (example):
  - `SECURE_ANALYZER_URL=http://secure-analyzer:5070`
  - `SUMMARIZER_HUB_URL=http://summarizer-hub:5060`
  - (Optional) `BEDROCK_ENDPOINT=http://localhost:7090/invoke` for proxy mode

## 1) Suggest models (policy-aware)
```
POST /summarization/suggest (orchestrator)
{
  "content": "This document includes an API key and client name for ACME.",
  "keywords": ["client name", "api key"]
}
```
Response includes a suggestion and a summarization result executed with secure models:
```
{
  "suggestion": {"sensitive": true, "allowed_models": ["bedrock","ollama"], ...},
  "result": {"summaries": {"bedrock": "..."}, "analysis": {...}}
}
```

## 2) Override policy (allow any provider)
```
POST /summarization/suggest
{
  "content": "Contains proprietary roadmap notes.",
  "override_policy": true
}
```
The orchestrator will allow any providers (default set) for summarization.

## 3) Non-sensitive content
```
POST /summarization/suggest
{
  "content": "Public release notes: Added /health endpoint; minor UI fixes."
}
```
Allowed models will include non-secure providers.

## Notes
- `secure-analyzer` uses default patterns and user-supplied keywords/URL to detect sensitivity.
- When `sensitive=true` and no override, only Bedrock/Ollama are permitted.
- For local dev, point `summarizer-hub` to `BEDROCK_ENDPOINT` and run the `bedrock-proxy` stub.
