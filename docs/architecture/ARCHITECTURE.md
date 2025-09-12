# Architecture Overview

## System map
```
[CLI] ──► [Interpreter] ──► [Orchestrator] ──► [Source Agent] ──► [Doc Store]
                      │                  └──► [Analysis Service]
                      │                         └──► [Notification Service]
                      └──► [Prompt Store]

[Secure Analyzer] ─► [Summarizer Hub]
[GitHub MCP] ───────────────────────► [Code Analyzer] ─► [Doc Store]

All services ─► [Log Collector]
```

## Common patterns
- FastAPI + shared middleware (request id, metrics)
- Standard health endpoints and success/error envelopes
- Service discovery via Orchestrator registry (selected services self-register)
- Tests organized per-service under `tests/unit/<service>`

## Envelopes
- Success envelope: `{ "success": true, "data": {...}, "message": "...", "request_id": "..." }`
- Error envelope: `{ "success": false, "error_code": "...", "details": {...}, "request_id": "..." }`

## Key responsibilities
- Interpreter: intent recognition and workflow creation
- Prompt Store: prompt CRUD, A/B testing, analytics
- Analysis Service: consistency checks, reports
- Doc Store: content, analyses, search, quality
- Source Agent: ingest and normalization from GitHub/Jira/Confluence
- Orchestrator: registry, workflows, jobs
- Secure Analyzer + Summarizer Hub: policy-aware summarization
- Code Analyzer: code endpoint detection and examples
- Log Collector: centralized logs and stats

## Observability
- Health: `/health` (and some `/ready`)
- Metrics/logging: middleware + optional external backends

## Data flow examples
- Analyze query
  1) CLI/Frontend → Interpreter `/interpret`
  2) Interpreter creates workflow → Orchestrator/Analysis/Doc Store as needed
- Prompt retrieval
  - Services/CLI → Prompt Store `/prompts/search/{category}/{name}`

## Configuration
- Centralized helpers in `services/shared` (config, clients, constants)
- Prefer env and YAML-based defaults where available
