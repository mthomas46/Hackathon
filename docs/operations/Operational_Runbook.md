# Operational Runbook

Last updated: 2025-09-08

## Overview

Operational guidance for the local multi-service documentation consistency ecosystem under `services/*`.

Shared modules:
- `services/shared/config.py` — load YAML configs per-service
- `services/shared/constants.py` — env keys and headers
- `services/shared/clients.py` — retried JSON HTTP helpers
- `services/shared/owners.py` — owner extraction, CODEOWNERS helpers

## Environments and Common Variables

- Core
  - `REDIS_HOST` (optional): host:port for Redis pub/sub.
  - `LOG_COLLECTOR_URL` (optional): base URL for centralized logs.
  - `ORCHESTRATOR_PEERS` (optional): comma-separated peer orchestrator base URLs for registry replication.

- LLM
  - `OLLAMA_HOST`: URL for Ollama (shared or sidecar), e.g. `http://ollama:11434`.
  - `OLLAMA_MODEL`: default model (e.g., `llama3`).
  - `RATE_LIMIT_ENABLED`: enable RateLimitMiddleware when `true|1|yes` (defaults off for tests).

- Providers (optional)
  - `BEDROCK_*`: AWS Bedrock configuration (if enabled in summarizer-hub).
  - `SUMMARIZER_HUB_URL`: for secure-analyzer.
  - `NOTIFICATION_URL`: base for notification-service.
  - `DOC_STORE_URL`: base for doc-store.

## Services and Health

Each service exposes `GET /health`.

- Orchestrator: control plane, registry at `/registry/*`.
- Agents: github-agent, jira-agent, confluence-agent, swagger-agent.
- Consistency Engine: analysis entrypoint (TBD APIs as implemented).
- Memory Agent: stores summaries and findings.
- Reporting: report generation endpoints.
- Summarizer Hub / Secure Analyzer: LLM orchestration and policy.

## Typical Workflows

1) Start Stack (local)
   - Start Redis (optional) and Ollama.
   - Start FastAPI services under `services/*` (dev servers or compose when available).

2) Ingest and Analyze
   - Trigger ingestion via orchestrator or directly call agents.
   - Consistency engine consumes events or is called directly to run checks.
   - Findings stored in memory-agent; reporting can render Life of Ticket / PR Confidence / Log Analysis / Trends / Confluence Consolidation / Jira Staleness (duplicates; optional summary) / ADR Drift / Jira AC Coverage.
   - When enabling rate limits in `code-analyzer` or `summarizer-hub`, set `RATE_LIMIT_ENABLED=true` and restart services.

3) Summarization
   - Use summarizer-hub for ensemble or provider-specific calls.
   - Secure-analyzer proxies sensitive requests with policy constraints.

## Troubleshooting

- No findings generated
  - Verify events are emitted (if Redis enabled) and CE subscriptions are active.
  - Check `content_hash` and debouncing; repeated identical inputs are intentionally skipped.

- LLM requests slow or failing
  - Confirm `OLLAMA_HOST` and model availability; warm up models.
  - Reduce concurrency or use per-service sidecars to isolate load.

- Missing documents in reports
  - Ensure agents normalized documents; inspect `Document` payloads and `content_hash`.
  - Check reporting service connectivity to CE and memory-agent.
  - Shared clients: most JSON HTTP calls use `ServiceClients` with retries; if a dependency is flapping, check backoff and service health.
  - For owner-targeted notifications, verify `NOTIFICATION_URL` is reachable and mappings provided via `NOTIFY_OWNER_MAP_JSON` or `NOTIFY_OWNER_MAP_FILE`.

## Operational Tips

- Propagate `X-Correlation-ID` across calls for traceability.
- Use ETag/If-None-Match or Last-Modified for upstream fetches.
- Keep LLM checks behind flags; prefer rule-based detectors first.
- Apply timeouts and small jittered retries on cross-service calls.
- Use `/reports/findings/notify-owners` and `/reports/confluence/notify-owners` for targeted alerts; consider a weekly cron invoking orchestrator `/jobs/recalc-quality` and `/jobs/notify-consolidation`.
- For Jira hygiene, schedule `/reports/jira/staleness` with filters (e.g., `?min_confidence=0.5&min_duplicate_confidence=0.6&limit=50&summarize=true`) and route outputs to owners.
- Consider adding `/reports/adr_drift` and `/reports/jira/ac_coverage` to weekly hygiene dashboards.


