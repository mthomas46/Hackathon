# Librarian – Living Document

Goal: Multi-pass analysis and feature plan aligned to the doc-consistency ecosystem.

## Pass 1: Surface Overview
- Documentation and contextual reference system; ingestion, analyzers, dashboards.

## Pass 2: API & Core
- FastAPI app pattern; analyzers for README/dependencies/relationships; static lists.

## Pass 3: Indexing & Search
- Deep Cerebro/Elasticsearch integration; analytics; suggestions; events.

## Pass 4: Security & Policy
- Integrations for LawMan, LockBox, Rolodex; user association and policies.

## Pass 5: Infrastructure Analysis
- Dockerfile/build/script parsing; dependency conflict detection; cross-app analysis.

## Pass 6: Gaps & Risks
- Not directly LLM-integrated today; needs alignment with canonical models/events.

## Feature Plan (Portal)
- Containerize lightweight Librarian portal later; for now, integrate with reporting/frontend.
- Provide dashboards for coverage, drift hotspots, severity heatmaps.
- Optional: index findings and link back to source docs for traceability.

## Interop Contracts
- Consume normalized Document/ApiSchema/Finding; expose dashboards and search.

## Deep Dive (10 Passes)
1) API endpoints in `api/app.py`: `/health`, `/ready`, `/config`, `/config/validate`, `/`, `/api/v1`.
2) Routes scaffold: `static-lists` APIRouter exists; extend for document search and findings.
3) Analyzers: README, dependency, relationship analyzers; port pieces into Consistency Engine rules.
4) Cerebro integration: advanced search/analytics; later wire via separate search service.
5) Static lists: tag categories and ecosystem apps; use to enrich findings and coverage views.
6) Infrastructure analysis: docker/build parsing; feed into drift checks (docs vs infra).
7) Security & Policy: LawMan/LockBox integrations; incorporate as future capabilities.
8) Config system: hydra-like config; keep lighter config in Hackathon for now.
9) Tests: unit/integration for ingestion and integrations; model for our test plan.
10) Mapping: leverage dashboard ideas in Frontend; later a full portal using Librarian patterns.
