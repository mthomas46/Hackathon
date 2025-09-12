# LlamalyticsHub – Living Document

Goal: Multi-pass analysis and feature plan aligned to the doc-consistency ecosystem.

## Pass 1: Surface Overview
- FastAPI app for code analysis & GitHub audits; strong security layer; good testing.

## Pass 2: API & LLM Client
- Endpoints for text, upload, PR analysis; detailed `ollama_client.py` with sync/async calls.

## Pass 3: Docker & Config
- Compose includes Ollama and app; env-driven configuration; Make targets for health.

## Pass 4: Security
- Validation, rate limiting, headers; advanced middlewares; status/threat endpoints.

## Pass 5: Testing & CI-readiness
- High coverage; categorized tests; clear run modes.

## Pass 6: Gaps & Risks
- Needs canonical normalization and event emission for ecosystem integration.

## Feature Plan (GitHub Agent)
- Implement endpoints in Hackathon `github-agent` for:
  - PR analysis (diff summary, doc delta), README/doc extraction.
  - Normalization into Document schema; emit `docs.ingested.github`.
  - Optional: map PR to Jira via branch naming/links.
- LLM prompts for README vs OpenAPI drift detection.

### Update: Code Analysis Plan
- New endpoints to add:
  - `POST /code/analyze`: Accepts file/url; extracts endpoints, key symbols, and produces a `Document` with code insights.
  - `POST /pr/review`: Given PR JSON or repo/PR number, run code review summary, list added/changed endpoints and risks.
- Cross-source leveraging:
  - Consistency Engine compares extracted endpoints vs Jira AC and Confluence pages; raises findings on mismatch/missing docs.
  - Summaries also passed to summarizer-hub for ensemble agreement.

## Interop Contracts
- HTTP: `/analyze/pr`, `/docs/{repo}`, etc. (to extend)
- Events: `docs.ingested.github`.

## Deep Dive (10 Passes)
1) Endpoints: `/`, `/health`, `/reports`, `/logs`, `/endpoints`, `/generate/text`, `/upload`, `/generate/github-pr`, `/reports/{name}`, security routes; archive shows similar endpoints.
2) LLM Client: `ollama_client.py` sync/async, batch, extensive logging; reuse prompt patterns for drift detection.
3) Security: Middlewares for headers, validation, rate limiting; adopt in agent incrementally.
4) Docker & Make: health targets; keep for dev.
5) Reporting: Writes reports dir, list/get endpoints; map into Reporting service ingestion.
6) Testing: Many tests including performance; use as reference for our agent tests.
7) Config: env + config.yaml template, precedence; replicate minimal subset.
8) Logging: Rotating logs, error surfacing; integrate with centralized logging later.
9) Gaps: Need canonical normalization + event emission; add Repository doc extraction endpoints.
10) Mapping: `github-agent` to implement PR audit + README extraction; emit `docs.ingested.github` with normalized payloads.
