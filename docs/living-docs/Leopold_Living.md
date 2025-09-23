# Leopold – Living Document

Goal: Capture multi-pass analysis and a concrete feature plan aligned to the doc-consistency ecosystem.

## Pass 1: Surface Overview
- Central orchestration platform with plugin system and rich docs.
- Integrates many services; strong security/monitoring posture.

## Pass 2: API & Config
- FastAPI server with `/workflows/execute`, health, metrics.
- Config (`config/leopold.yaml`) shows LLM provider (Ollama), ecosystem URLs.

## Pass 3: Orchestration & Plugins
- Plugin manager, registry, orchestration templates; needs completion breadth across services.

## Pass 4: Deployment & Sidecars
- Compose files include Redis/Ollama and multiple services; adaptable to per-service sidecars.

## Pass 5: Testing & Docs
- Extensive docs and tests; opportunity to add workflows for doc-consistency pipeline.

## Pass 6: Gaps & Risks
- Some plugins in-progress; cross-service workflow catalog incomplete; needs specific contracts for new agents.

## Feature Plan (Leopold-as-orchestrator)
- Add workflows:
  - `ingest_all`: trigger GitHub, Jira, Confluence, Swagger agents; await `ingestion.completed`.
  - `analyze_consistency`: call Consistency Engine with target sets; aggregate findings.
  - `report_and_notify`: call Reporting; post to endpoints (future Confluence/Jira comments).
- Add health/metrics aggregation per agent.
- Add event bus publisher/subscriber (Redis) and correlation tracking.
- Secure service-to-service HMAC option.

## Interop Contracts
- Support our canonical topics and HTTP endpoints as defined in the Hackathon living doc.

---

Owner notes:
- When rewriting Leopold locally, keep it thin and publish/coordinate via events.

## Deep Dive (10 Passes)
1) Endpoints Inventory (from api/*): `/`, `/health`, `/tools`, `/execute`, `/workflow`, `/agentic/*`, `/ecosystem/*`, `/workflows/execute`, `/integrations`, `/metrics`.
2) Workflow Semantics: Templates for security testing, data analysis, chaos testing; extend to doc-consistency: ingest → analyze → report.
3) Plugin Surface: Hotline, LogBlanc, SpeedForce, DrBones, etc.; define lightweight shims to our Hackathon agents.
4) Config & Providers: LLM provider defaults to Ollama; ensure `OLLAMA_HOST` is optional in orchestrator (use agents for LLM work).
5) Health/Telemetry: Prometheus metrics endpoint; aggregate per-agent status via health routers; expose ecosystem roll-up.
6) Error Handling: Standardized success/error responses; reuse patterns in orchestrator service.
7) Security: CORS, auth middleware hooks; add service-to-service HMAC.
8) Deployment: Compose variants; adopt sidecars pattern and private networks; no port publish for Ollama.
9) Tests: Add workflow tests for `ingest_all`, `analyze_consistency`, `report_and_notify` once Redis events are integrated.
10) Mapping to Hackathon: Orchestrator emits `ingestion.requested`, awaits `docs.ingested.*`, invokes Consistency Engine `/analyze`, then Reporting `/reports/generate`.
