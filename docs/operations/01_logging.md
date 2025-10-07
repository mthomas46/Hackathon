---
llm_metadata:
  document_type: guide
  content_focus: technical
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - monitoring
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about technical aspects of the shared platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# Logging Integration

All services can emit structured logs to the local `log-collector`.

- Helper: `services.shared.logging.fire_and_forget(level, message, service, context=None)`
- Endpoint: `POST {LOG_COLLECTOR_URL}/logs`
- Dev/Test: set `LOG_COLLECTOR_URL=http://testserver` to use in-process ASGI when tests run.
- Default: if `LOG_COLLECTOR_URL` is unset, emit is a no-op.

Currently instrumented services:
- orchestrator, github-agent, jira-agent, confluence-agent, swagger-agent, reporting (incl. reports), secure-analyzer, summarizer-hub, memory-agent, consistency-engine.

The reporting service exposes `/reports/log_analysis` to generate insights from collected logs.

## Demo bundle via Orchestrator
- Endpoint: `POST /demo/e2e`
- Example:
```bash
curl -s -X POST "$ORCHESTRATOR_URL/demo/e2e" -H 'content-type: application/json' -d '{"format":"json","log_level":"error","log_limit":20}' | jq .
```
This returns a JSON object with `summary` and `log_analysis` built by the reporting service.
