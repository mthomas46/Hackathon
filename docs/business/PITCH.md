# Documentation Consistency Ecosystem – Demo Pitch

## The idea (30 seconds)
Your docs, tickets, and API contracts drift every week. This system continuously ingests GitHub, Jira, Confluence, and OpenAPI; detects contradictions and staleness; and gives you focused, actionable reports with owners attached. It’s modular, quick to stand up, and built on rule‑first detectors with LLMs used only where they add signal.

## What we’ll show (2–3 minutes)
- Detect drift and contradictions:
  - README vs OpenAPI error‑code mismatches
  - Jira Acceptance Criteria vs Confluence content
- Jira hygiene at a glance:
  - Jira Staleness report with duplicate detection and optional summary
  - Acceptance Criteria Coverage (what’s documented vs what’s missing)
- Confluence cleanup:
  - Orphan/Duplicate Finder with confidence scores and suggested merges
- Actionability:
  - Auto Doc‑PR suggestions (targets README or Confluence)
  - Owners/Reviewers derived from CODEOWNERS and metadata
- UI and exports:
  - Frontend views (findings, quality, consolidation, Jira staleness)
  - Report snapshots and JSON/Markdown export

## Why it matters (outcomes)
- Keep docs and APIs trustworthy with minimal process overhead
- Shorten review cycles by surfacing owners and evidence automatically
- Catch drift before release; reduce on‑call ambiguity and ticket thrash

## How it works (at a glance)
- Orchestrator coordinates workflows and a simple service registry
- Agents normalize sources: GitHub, Jira, Confluence, Swagger/OpenAPI
- Consistency Engine batches inputs and runs detectors (rule‑first + LLM‑assisted)
- Reporting aggregates into trends and targeted reports; triggers notifications
- Doc Store persists documents, search (FTS5 + semantic fallback), and quality flags
- Frontend provides a minimal, fast portal for findings and reports

Shared standards: YAML config loader with precedence (env > `config/app.yaml` > defaults), JSON ServiceClients (retries/timeouts/circuit), correlation IDs, request metrics, versioned envelopes, and consistent error handling.

## Live demo script (suggested)
1) Kick off ingestion via Orchestrator
2) Open Frontend findings and by‑severity views
3) Show Reporting → Confluence Consolidation (owners, flags) and Jira Staleness (duplicates + summary)
4) Export a report snapshot and display JSON/Markdown
5) Trigger Auto Doc‑PR suggestions and show owners/reviewers mapping

## Capabilities (today)
- Detectors: README/OpenAPI error‑code mismatch; Jira AC vs Confluence; drift candidates
- Reports: Trends, Life‑of‑Ticket, Confluence Consolidation, Jira Staleness (duplicates + summary), ADR Drift, Jira AC Coverage
- Action tooling: Auto Doc‑PR suggestions; Owners/Reviewers resolution; Notification DLQ proxy
- Doc Store: `/documents/enveloped`, FTS5 search with semantic fallback, quality flags, and listing
- Frontend: findings, search, quality, consolidation, Jira staleness; raw JSON toggles ready
- Operability: `/health`, `/ready` (where applicable), `/info`, `/config/effective`, `/metrics`; standardized error handlers

## Differentiation
We prioritize stable, explainable detectors and use LLMs as an assist—not a dependency. Contracts are envelope‑based, tests are realistic and fast, and each service stands alone or together. You can onboard incrementally and keep full control over providers.

## Getting started
- Bring up Orchestrator, Doc Store, Analysis Service, Source Agent, and Frontend
- Point agents at your repos/spaces and set minimal env configs
- Visit Frontend to view findings; hit Reporting endpoints for reports and exports

## One‑liner
Make your documentation reliable again—detect drift early, route to the right owners, and ship with confidence.

## Why now
- Toolchains and teams move fast—docs drift faster than ever. A lightweight, analyzable system that favors rules and clear ownership beats opaque “AI doc bots.”
- Drop‑in services and a minimal UI let teams start small, add depth later.

## Business value (bullets for slides)
- Reduce doc-related incidents and on-call time
- Faster onboarding with trustworthy docs
- Shorter PR review cycles via auto‑suggested doc updates and owners
- Evidence‑backed audits for compliance and post‑mortems

## Run it in minutes
```bash
# Local dev (live code)
docker compose -f docker-compose.dev.yml up -d redis orchestrator doc_store analysis-service source-agent frontend

# Open the UI
open http://localhost:3000
```


