# AvettaConfluenceDownloader – Living Document

Goal: Multi-pass analysis and feature plan aligned to the doc-consistency ecosystem.

## Pass 1: Surface Overview
- CLI + Flask server for Confluence crawling, caching, and metrics; LLM combine.

## Pass 2: API & CLI
- `llm_server.py` wrapper to Ollama; `cli.py` orchestrates downloads; rich analytics/metrics.

## Pass 3: Analytics
- Coverage, churn, redundancy, ownership; robust logs and error handling.

## Pass 4: LLM Integration
- Uses Ollama or external models to summarize and merge docs; caching around LLM steps.

## Pass 5: Configuration & Batching
- YAML-driven batch configs; multi-parent workflows; resume and caching.

## Pass 6: Gaps & Risks
- Server endpoints mostly stubs in `server.py`; needs canonical normalization and events.

## Feature Plan (Confluence Agent)
- Implement endpoints in Hackathon `confluence-agent` for:
  - Crawl by space/page; cache text and metadata.
  - Summarize pages with Ollama sidecar; normalize into Document schema.
  - Emit `docs.ingested.confluence` with correlation ids.
- Add derived quality metrics for doc consistency and staleness.

## Interop Contracts
- HTTP: `/summarize/page`, `/crawl`, `/space/{key}`, `/page/{id}` (to extend)
- Events: `docs.ingested.confluence`.

## Deep Dive (10 Passes)
1) Server endpoints (Flask): health, llm summarize/metadata, crawl, space/page fetch, search; diagnostics endpoint.
2) LLM server wrapper: `/llm/generate` proxied to Ollama with model gating.
3) Analytics: churn, coverage, redundancy, quality, ownership; useful signals for Reporting.
4) Caching: stores page text and llm results; preserves progress across runs.
5) CLI orchestration: batch configs with multi-parent support; automate crawl flows.
6) Logging & Error handling: robust logs, restarts; integrate patterns.
7) Metrics outputs: markdown and JSON; importable to our Reporting.
8) Configuration: YAML + env; reuse keys when building adapters.
9) Gaps: API stubs need implementations for our agent; normalization missing.
10) Mapping: `confluence-agent` to implement crawl + summarize + normalize; emit `docs.ingested.confluence` with payloads.
