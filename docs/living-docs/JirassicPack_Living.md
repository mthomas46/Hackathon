# JirassicPack – Living Document

Goal: Capture multi-pass analysis and a feature plan aligned to the doc-consistency ecosystem.

## Pass 1: Surface Overview
- Themed CLI for Jira with analytics, bulk ops, docs generation; LLM integration.

## Pass 2: API/Server & Config
- Flask HTTP API available; CLI front-end; `.env` and YAML configs; batch mode.

## Pass 3: Features & Outputs
- Strong markdown reports; time tracking; team analytics; PR link scraping from comments.

## Pass 4: LLM & Sidecar
- Local Ollama integration pathway; can be proxied; API key gating available in HTTP API.

## Pass 5: Strengths & Tooling
- Robust error handling; structured logs; manifest-driven CLI; examples and templates.

## Pass 6: Gaps & Risks
- HTTP API is not full-featured; needs normalization and clear contracts for ecosystem use.

## Feature Plan (Jira Agent)
- Implement API endpoints in Hackathon `jira-agent` to:
  - Fetch issue(s), sprints/boards, acceptance criteria fields.
  - Summarize tickets via Ollama sidecar; normalize into Document schema.
  - Emit `docs.ingested.jira` with correlation ids.
- Add consistency checks specific to Jira AC vs README/API.
- Optional: webhook to comment findings back to Jira.

## Interop Contracts
- HTTP: `/summarize/issue`, `/boards`, `/sprints?board_id` (to be added), etc.
- Events: `docs.ingested.jira`.

## Deep Dive (10 Passes)
1) Endpoints (Flask http_api): `/help`, `/health`, `/logs`, `/endpoints`, `/config`, `/analytics/export`, `/auth/*`, `/system/*`, `/docs`, `/jira/*` (projects, users, boards, sprints, transitions, comment, assign).
2) LLM API (llm_api): `/llm/stats`, `/status`, `/health`, `/logs`, `/generate/*`, `/endpoints` for local analysis.
3) CLI Features: advanced metrics, team analytics, summarization, bulk ops, automated docs.
4) Config Patterns: `.env`, YAML single/batch, robust validation.
5) Reporting: Markdown outputs in `output/`, structured logs; potential sources for Reporting service.
6) Error Handling: consistent logging, retries; preserve when porting.
7) Security: optional API key gating; maintain behind internal network.
8) Gaps: No canonical normalization; add Document schema emitter.
9) Mapping: Implement Jira fetch + normalize in `jira-agent`; reuse menu logic for selecting targets later.
10) Events: Emit `docs.ingested.jira` upon summarization and ingestion completion; include correlation_id.
