# LLM-Orchestrated Documentation Consistency Ecosystem (Living Document)

This is the living plan and operational log for building a multi-microservice, agent-based ecosystem that ingests documentation and signals from GitHub, Jira, Confluence, and OpenAPI/Swagger, then detects and summarizes inconsistencies.

Last updated: 2025-09-05

## 1) Vision and Scope

- Build an orchestration-first system to continuously ingest product and engineering documentation signals and surface inconsistencies.
- Primary sources: GitHub (code/PRs/READMEs), Jira (issues/sprints), Confluence (spaces/pages), OpenAPI/Swagger (API truth).
- Output: reports, alerts, dashboards, and actionable remediation guidance.

## 2) Current Capabilities Snapshot

 - All FastAPI microservices implemented locally under `services/*`, each with `config.yaml`.
 - Orchestrator provides health, ingestion workflow, and a registry with discovery-agent auto-registration.
 - Shared models define `Document`, `ApiSchema`, `Finding`, `MemoryItem` for normalized exchange.
 - Consistency Engine performs batch analysis with debouncing and README drift checks. Summarizer-hub integration stubs; outputs stored in memory-agent.
 - Summarizer Hub supports provider-agnostic ensemble (Ollama, OpenAI, Anthropic, Grok-ready), returns agreed summary + diffs.
 - Memory Agent stores operational and LLM summaries; subscribes to key events.
 - Discovery Agent ingests inline/OpenAPI specs and registers services with orchestrator (supports in-process testserver). All services self-register on startup.
 - Reporting generates: Summary, Life of the Ticket, PR_Confidence, Log Analysis, Trends, Confluence Consolidation, Jira Staleness (duplicates + optional summary), ADR Drift, Jira AC Coverage, Duplicate Clusters, Auto Doc-PRs, Doc Owners/Reviewers, Doc Accuracy Badges, Topic Hubs, and Confluence Orphans/Duplicates. Frontend provides findings by severity/type, search, quality signals, consolidation, Jira Staleness, and Duplicate Clusters views.
 - Shared utilities standardized: `services/shared/config.py` (YAML loader), `services/shared/constants.py` (env keys/headers), `services/shared/clients.py` (retried JSON HTTP), `services/shared/request_id.py` (correlation), `services/shared/metrics.py` (request logs).
 - Ingestion jobs: Analytics (views/watchers), Jira activity (transitions/comments), Confluence structure (labels/parents), GitHub blame/release/doc-commits, Confluence backlinks, Jira fields (due/resolution/activity).
 - Webhooks: Jira, Confluence, and GitHub webhooks for real-time metadata updates.
 - Doc Store enhancements: Content length tracking, thin content flagging, metadata patching for analytics.

## 3) Target Microservices and Responsibilities

1. Orchestrator (Leopold)
   - Owns workflows, schedules periodic ingestion, aggregates results.
   - Exposes control plane API and metrics.

2. LLM Runtime (Ollama)
   - Local inference for summarization and consistency checks.

3. Message Bus (Redis)
   - Pub/sub for events: ingestion.started, ingestion.completed, findings.created.

4. GitHub Agent (LlamalyticsHub)
   - Fetches repo docs, PRs, READMEs. Produces normalized Document entities, PR diffs, and doc summaries.

5. Jira Agent (jirassicPack)
   - Fetches issues/boards/sprints, relevant fields (Descriptions, Acceptance Criteria). Emits normalized records.

6. Confluence Agent (AvettaConfluenceDownloader)
   - Crawls spaces/pages, caches content, emits page text, metadata, and derived metrics.

7. Swagger/OpenAPI Agent (new, placeholder)
   - Fetches OpenAPI specs from repos/URLs. Emits canonical API schema documents.

8. Consistency Engine (new, placeholder)
   - Consumes normalized docs and APIs; runs rule-based + LLM-based checks; writes Findings.

9. Librarian Portal (later phase)
   - Presents dashboards, coverage, knowledge graph of docs ↔ code ↔ issues ↔ APIs.

## 4) Inter-Service Contracts (Stable v1)

- Event Topics (Redis pub/sub):
  - ingestion.requested: {source: github|jira|confluence|swagger, scope, correlation_id}
  - ingestion.completed: {source, item_count, correlation_id, artifacts[]}
  - findings.created: {correlation_id, count, severity_counts}
    - Severity thresholds (by detector score): score≥80 → high, score≥60 → med, score≥30 → low

### Envelope Shapes
- DocumentEnvelope
  - id, version, correlation_id, source_refs[], content_hash, timestamp, document{}
- ApiSchemaEnvelope
  - id, version, correlation_id, source_refs[], content_hash, timestamp, schema{}

Producers emit envelopes on:
- docs.ingested.github|jira|confluence → DocumentEnvelope
- apis.ingested.swagger → ApiSchemaEnvelope

- HTTP Contracts (selected):
  - github-agent
    - GET /health
    - GET /reports
    - POST /generate/github-pr {owner, repo, pr?}
    - GET /endpoints
  - jira-agent
    - GET /health
    - GET /jira/projects|users|boards|sprints?board_id
    - POST /jira/issue/{transition|comment|assign}
  - confluence-agent
    - GET /health
    - POST /confluence/crawl
    - GET /confluence/space/{key}
    - GET /confluence/page/{id}
  - swagger-agent (TBD)
    - POST /ingest {url|path}
    - GET /specs
  - consistency-engine (TBD)
    - POST /analyze {targets:[docIds|apiIds|issueIds]}
    - GET /findings?since=...

## 5) Canonical Data Model (v1)

- Document
  - id, source_type (github|jira|confluence|swagger), source_id
  - title, content, content_hash
  - path/url, project_key/repo, timestamp, metadata{}

- ApiSchema
  - id, service_name, version, openapi_json, endpoints[] {path, method, params, response, description}

- Finding
  - id, type (missing_doc|contradiction|drift|stale|broken_link|schema_mismatch|acceptance_mismatch|security_gap)
  - severity (low|med|high|crit), source_refs[], description, evidence[], suggestion
  - detected_at, detector_version, correlation_id

## 6) Detection Approach

1. Heuristic rules (fast, deterministic):
   - Broken links, empty sections, outdated timestamps, cross-file keyword mismatches.
   - PR summary vs README drift; Jira AC vs README feature claims; OpenAPI description vs README endpoints.

2. LLM-assisted checks (Ollama):
   - Summarize page/issue/PR; compare summaries across sources for contradictions.
   - Ask: "Does README claim endpoint X that is missing in OpenAPI?"; "Does Jira AC conflict with API schema?".

3. Aggregation and ranking:
   - Merge duplicate findings; score by blast radius (services touched), recency, severity.

## 7) Security and Secrets

- Do not bake tokens into images. Use env vars: GITHUB_TOKEN, JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, CONFLUENCE_*.
- Least-privilege API scopes. Optional service-to-service auth via HMAC header between orchestrator and agents.

## 8) Deployment & Observability (Initial)

- Compose single-host for P0/P1 with Redis + Ollama + agents + orchestrator.
- Health/metrics endpoints exposed; centralized in-memory log collection via `log-collector` (dev) with future path to external backends.

### Caching Policy
- Agents SHOULD use HTTP caching when fetching upstream content:
  - GitHub/Jira: ETag + If-None-Match
  - Confluence: Last-Modified + If-Modified-Since (ETag when available)
- Normalized `Document` includes `content_hash`, `version_tag`, and `last_modified` to enable idempotent ingestion.

### Drift Monitoring
- Orchestrator provides `POST /registry/poll-openapi` to recompute schema hashes and raise `api_drift_candidate` (low) on change. Multiple orchestrators can replicate registries via `ORCHESTRATOR_PEERS` and `/registry/sync-peers`.

### Memory
- Memory-agent stores summaries/findings with TTL cleanup and a lightweight inverted index keyed by endpoint path.

## 9) Phased Plan and Milestones (historic)

- P0 (Day 1-2):
  - Bring up Redis, Ollama, Leopold, LlamalyticsHub (github-agent), jirassicPack (jira-agent), Confluence server stub.
  - Manual end-to-end: fetch sample docs, run one LLM comparison, produce markdown report.

- P1 (Week 1):
  - Add swagger-agent skeleton; normalize outputs; wire basic Redis events.
  - Consistency Engine minimal version: drift between README <-> OpenAPI; basic Jira AC vs README.

- P2 (Week 2-3):
  - Expand rule set; add summarization-based contradiction checks.
  - Introduce Librarian portal/docker and dashboards.

- P3 (Week 4+):
  - Hardening, auth between services, error budgets, SLOs; add Prometheus/Grafana.

## 10) KPIs

- Coverage: % repos/services with OpenAPI + README ingested.
- Detection precision/recall (manual sample verification).
- MTTR for resolving inconsistencies after alert.
- Pipeline latency: ingestion -> finding emitted.

## 11) Open Questions / Risks

- Librarian run mode requires Hydra config flow — containerization needs a small wrapper.
- jirassicPack and Confluence services lack Dockerfiles — use base image and runtime pip install initially, add Dockerfiles in P1.
- Access to enterprise Jira/Confluence — rate limits and auth.

## 12) Execution Log

- [<PLAN_START>] Created living doc and docker-compose skeleton; defined contracts and data model v0.
- [2025-09-05] Rewrote services as local FastAPI apps; added discovery-agent, memory-agent, summarizer-hub, reporting, frontend. Implemented registry, batch analysis, README drift, and tests (all passing).
- [2025-09-05] Modularization pass: extracted logic modules (`github-agent/logic.py`, `confluence-agent/logic.py`, `swagger-agent/logic.py`, `discovery-agent/logic.py`), reporting utilities (`reporting/utils.py`), and added module docstrings across services.
- [2025-09-05] Infrastructure hardening: moved `consistency-engine` and `memory-agent` to FastAPI lifespan for event subscription; extracted `consistency-engine/events.py`; split reporting into routers (`reports/life_of_ticket.py`, `reports/pr_confidence.py`); added `shared/clients.py` for inter-service calls; test suite now 0 warnings.
- [2025-09-05] Summarizer-hub: Added optional native AWS Bedrock support via boto3 (SigV4) with YAML/env configuration; retained HTTP proxy fallback; added unit tests for native/proxy paths.
- [2025-09-05] Added `secure-analyzer` service for sensitive detection + policy-aware summarization; added orchestrator `/summarization/suggest` proxy; added local `bedrock-proxy` with canned templates for dev.
- [2025-09-05] Added `log-collector` service for centralized logs and Reporting `/reports/log_analysis`; tests and docs updated.

---

Appendix A: Minimal Redis Topics

```
docs.ingested.github
docs.ingested.jira
docs.ingested.confluence
apis.ingested.swagger
findings.created
```

## 13) Ollama Sidecar Strategy (Local and Secure LLM)

Observations from repos:
- Leopold: Defaults to provider "ollama" with `OLLAMA_HOST` and health checks; compose already includes an `ollama` service. Works with shared or sidecar endpoints.
- LlamalyticsHub: Uses `OLLAMA_HOST`, `OLLAMA_MODEL`, optional `OLLAMA_API_KEY`; compose binds to `http://ollama:11434`. Ready for sidecar or shared.
- jirassicPack: Uses `OLLAMA_HOST` and `OLLAMA_API_KEY`; CLI can boot `ollama serve`. Ideal candidate for a per-service sidecar in Docker.
- AvettaConfluenceDownloader: Wraps Ollama via `llm_server.py` with `OLLAMA_URL`; can point to a local sidecar for strict isolation.
- Librarian: No direct Ollama usage (today). Can defer to the Consistency Engine’s LLM calls or add optional LLM client later.

Standardize environment variables:
- `OLLAMA_HOST`: Base URL to Ollama (e.g., `http://ollama:11434` or sidecar hostname).
- `OLLAMA_MODEL`: Default model (e.g., `llama3`, `codellama:7b`).
- `OLLAMA_API_KEY`: Only used by services that proxy/gate requests (e.g., jirassicPack HTTP API), not by Ollama itself.

Deployment modes:
1) Shared Ollama (default dev mode)
   - Single `ollama` service on internal network, not publicly exposed beyond compose.
   - Pros: Simpler ops, single model cache; Cons: No per-service isolation.
   - Set: `OLLAMA_HOST=http://ollama:11434` for Leopold, LlamalyticsHub, jirassicPack, Confluence wrapper.

2) Per-service sidecar (hardened/prod mode)
   - Run one Ollama instance per agent for network isolation and blast-radius reduction.
   - Pattern in Docker Compose:
     - Create `ollama-<svc>` alongside `<svc>` and put both on a private network; do NOT publish Ollama’s port.
     - Configure `<svc>` to use `OLLAMA_HOST=http://ollama-<svc>:11434`.
   - Optional: share the same models volume across sidecars if storage is a concern, or keep per-service volumes for strict isolation.

Security posture:
- Do not expose Ollama to the host in prod; only inter-container access.
- If using a proxy wrapper (e.g., jirassicPack HTTP API or a thin Nginx sidecar), require `X-API-KEY` or HMAC on agent→wrapper calls.
- Restrict networks: each agent + its ollama sidecar on a dedicated private network; orchestrator reaches agents, not Ollama directly.
- Rate-limit heavy LLM endpoints in wrappers when available.

Operational guidance per service:
- Leopold (orchestrator): No direct LLM calls required; if needed, prefer talking to agents rather than Ollama. Keep `OLLAMA_HOST` configurable for diagnostics only.
- LlamalyticsHub (github-agent): Default shared Ollama in dev; enable sidecar in prod as `ollama-github`. Ensure `OLLAMA_HOST` and `OLLAMA_MODEL` set via env.
- jirassicPack (jira-agent): Use `ollama-jira` sidecar; set `OLLAMA_HOST` and `OLLAMA_API_KEY` at the agent layer if gating.
- Confluence (confluence-agent): Run `llm_server.py` and point it to `ollama-confluence` (sidecar). Do not publish Ollama; only publish the wrapper.
- Consistency Engine: If it needs LLM calls, use shared or `ollama-consistency` sidecar depending on workload isolation needs.

Compose implementation notes:
- Current skeleton uses a shared `ollama`. To switch to sidecars, duplicate the `ollama` service per agent (no published ports), rename to `ollama-<svc>`, and update each agent’s `OLLAMA_HOST` accordingly. Consider separate private networks per pair for strict least-privilege routing.

## 14) Rewrite Mode in Hackathon (no external repos in containers)

Objective: Implement first-class, local FastAPI services under `Hackathon/services` that mirror capabilities without importing the original repositories as containers.

What’s added:
- `services/orchestrator`: Control plane API, issues ingestion requests, future Redis pub/sub.
- `services/github-agent`: Minimal PR analysis endpoint; will call GitHub + LLM.
- `services/jira-agent`: Minimal issue summarization endpoint; will call Jira + LLM.
- `services/confluence-agent`: Minimal page summarization endpoint; will call Confluence + LLM.
- `services/swagger-agent`: Existing; for OpenAPI ingestion.
- `services/consistency-engine`: Existing; for findings generation.

Compose changes:
- Replace single shared `ollama` with per-service sidecars: `ollama-github`, `ollama-jira`, `ollama-confluence`, `ollama-consistency` (no published ports), each on a private network with its paired agent.
- Agents set `OLLAMA_HOST` to the corresponding sidecar hostnames.

Incremental enhancement plan:
1) Implement real client calls for GitHub/Jira/Confluence and normalize outputs to Canonical Data Model v0.
2) Add Redis events (`ingestion.*`, `findings.*`) and orchestrator workflow wiring.
3) Port proven logic from the original repos into the new services step-by-step (unit tests first) keeping licensing and attribution.
4) Add authentication between services and rate-limiting on LLM-bound endpoints.

## 15) Project Living Docs Index
- Leopold: `docs/Leopold_Living.md`
- JirassicPack: `docs/JirassicPack_Living.md`
- LlamalyticsHub: `docs/LlamalyticsHub_Living.md`
- Librarian: `docs/Librarian_Living.md`
- AvettaConfluenceDownloader: `docs/AvettaConfluenceDownloader_Living.md`
- Glossary: `docs/Glossary.md`
- Features & Interactions: `docs/FEATURES_AND_INTERACTIONS.md`

## 16) Roll-up Roadmap
- P0: Bring up services; shared contracts and sidecars; manual end-to-end run.
- P1: Normalization + events + minimal rules in Consistency Engine; basic Reporting + Frontend.
- P2: Expanded rules + LLM contradiction checks; Librarian portal dashboards.
- P3: Hardening, auth between services, SLOs, full monitoring.

## 17) Ecosystem Efficiency Assessment (Initial)
- Architecture: Sidecar Ollama per service reduces contention and blast radius; internal networks limit exposure.
- Orchestration: Events plus HTTP keep coupling low; orchestrator coordinates without tight dependencies.
- Discovery: New discovery-agent + orchestrator registry centralize API visibility; simplifies routing and monitoring.
- Memory: memory-agent captures operational context for cross-request continuity without heavy persistence.
- Throughput risks: Redis pub/sub fanout is lightweight; long-running LLM calls isolated per-agent; add rate limits where needed.
- Bottlenecks: If many concurrent LLM operations occur, per-service Ollama and model caching help; consider model pool sizing.
- Next optimizations: batch analysis in consistency-engine; debounce repeated ingestions; circuit breakers on failing services.

## 18) Current State Snapshot
- Core services live (standalone + compose): orchestrator, github-agent, jira-agent, confluence-agent, swagger-agent, consistency-engine, memory-agent, discovery-agent, reporting, frontend.
- New: summarizer-hub (multi-provider ensemble) integrated into consistency-engine and memory-agent.
- Registry: discovery-agent auto-registers services with orchestrator.
- Events: agents emit docs/apis ingested to Redis; consistency-engine subscribes, debounces, and batches.
- Tests: unit + integration for health, registry, normalization, batch findings, search/quality, consolidation, owners/notifications.

## 19) Feature Roadmap (Next 4–6 weeks)
- Week 1
  - GitHub agent: add code analysis endpoints: `POST /code/analyze` (file upload/url), `POST /pr/review` (PR-based analysis), emit normalized `Document` with code insights.
  - Cross-source checks: implement rules in consistency-engine comparing GitHub code analysis vs Jira AC and Confluence docs (e.g., endpoints declared in code but missing in docs/AC).
  - Add `findings.created` emission and capture in memory-agent; display in frontend.
- Week 2
  - Provider integrations in summarizer-hub: OpenAI/Anthropic real clients (env-based); configurable provider sets per run.
  - Reporting: add endpoints to generate diff reports per provider and cross-source consistency report (code vs AC vs docs vs OpenAPI).
- Week 3
  - Discovery: scheduled re-discovery of services; drift detection on service OpenAPI.
  - Security: service-to-service HMAC and rate limits on summarizer calls.
- Week 4+
  - Librarian portal integration for dashboards and search.
  - CI hooks to run consistency checks on PRs and Jira transitions.




## 20) Service Integration Matrix

| Service | HTTP dependencies (env) | Events In | Events Out | Orchestrator Integration | Logging |
|---|---|---|---|---|---|
| orchestrator | `REPORTING_URL`, `SECURE_ANALYZER_URL` | - | `ingestion.requested` (via Redis, when configured) | Proxies `/report/request`, `/summarization/suggest`; owns `/registry/*` | Uses `LOG_COLLECTOR_URL` |
| github-agent | `OLLAMA_HOST` | - | `docs.ingested.github` (when Redis configured) | Registered via discovery-agent | Uses `LOG_COLLECTOR_URL` |
| jira-agent | `OLLAMA_HOST` | - | `docs.ingested.jira` (when Redis configured) | Registered via discovery-agent | Uses `LOG_COLLECTOR_URL` |
| confluence-agent | `OLLAMA_HOST` | - | `docs.ingested.confluence` (when Redis configured) | Registered via discovery-agent | Uses `LOG_COLLECTOR_URL` |
| swagger-agent | - | - | `apis.ingested.swagger` (when Redis configured) | Registered via discovery-agent | Uses `LOG_COLLECTOR_URL` |
| consistency-engine | `GITHUB_AGENT_URL` (optional) | `docs.ingested.*`, `apis.ingested.swagger` | `findings.created` (planned) | Listed in registry; consumed by reporting | Uses `LOG_COLLECTOR_URL` |
| memory-agent | - | `ingestion.requested`, `docs.ingested.*`, `apis.ingested.swagger`, `findings.created` | - | Listed in registry | Uses `LOG_COLLECTOR_URL` |
| reporting | `CONSISTENCY_ENGINE_URL`, `DOC_STORE_URL`, `LOG_COLLECTOR_URL`, `NOTIFICATION_URL` | - | - | Orchestrator proxies via `/report/request` | Uses `LOG_COLLECTOR_URL` |
| summarizer-hub | `BEDROCK_*`, `OLLAMA_HOST` | - | - | Called by secure-analyzer and CE | Uses `LOG_COLLECTOR_URL` |
| secure-analyzer | `SUMMARIZER_HUB_URL` | - | - | Orchestrator proxies via `/summarization/suggest` | Uses `LOG_COLLECTOR_URL` |
| discovery-agent | `ORCHESTRATOR_URL` | - | Registers to `/registry/register` | Registers services with orchestrator | Uses `LOG_COLLECTOR_URL` |
| frontend | `REPORTING_URL`, `CONSISTENCY_ENGINE_URL` | - | - | Calls orchestrated backends | Uses `LOG_COLLECTOR_URL` |
| log-collector | - | - | - | Optional dependency for all services | N/A |
