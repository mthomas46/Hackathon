---
llm_metadata:
  document_type: guide
  content_focus: operational
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - docker
  - monitoring
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about operational aspects of the shared platform
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

# Infrastructure Setup

## Local (compose)
- Use docker-compose files if provided (`docker-compose.dev.yml`, `docker-compose.services.yml`).
- Example:
```bash
docker compose -f docker-compose.dev.yml up -d
```

## Secrets
- Use `.env.local` (never commit) or docker secrets.
- Example `.env.local`:
```bash
EXTERNAL_GITHUB_TOKEN=ghp_xxx
EXTERNAL_AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
BEDROCK_API_KEY=...
```

## Observability
- Health: `/health` endpoints on each service
- Logs: `services/log-collector` for dev/test

## Networking
- Default ports: Prompt Store 5110, Interpreter 5120, Log Collector 5080, Orchestrator 5099
