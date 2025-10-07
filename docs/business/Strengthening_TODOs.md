---
llm_metadata:
  document_type: planning
  content_focus: technical
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - python
  - testing
  - security
  - monitoring
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about technical aspects of the shared platform
  archive_reason: n/a
  historical_value: current
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# Short-Term Strengthening TODOs

Timeframe: next 1–2 weeks. Scope-preserving improvements focused on hardening, determinism, and ops.

## Tasks

1. Add request validation for envelopes at ingress points (Pydantic models)
   - Services: orchestrator, agents, consistency-engine.
   - Outcome: malformed envelopes rejected with 400; consistent schema enforcement.

2. Implement simple rate limiting on LLM and heavy analysis endpoints
   - Token-bucket middleware per-service; configurable limits.
   - Outcome: protected from bursty traffic; predictable latency.

3. Enforce correlation ID propagation
   - Middleware injects `X-Correlation-ID` if absent; log it in all requests.
   - Outcome: traceability across services and reports.

4. Add retries with jitter and timeouts for cross-service calls
   - Centralize in `shared/clients.py` helpers.
   - Outcome: resilience to transient failures without thundering herd.

5. Batch and debounce in consistency-engine by correlation_id + content_hash
   - Ensure idempotency; skip identical reprocessing.
   - Outcome: improved throughput and reduced duplicate findings.

6. Expand rule-first detectors; gate LLM checks behind feature flags
   - Config: `detectors.enable_llm` and thresholds.
   - Outcome: deterministic baseline; lower cost and variance.

7. Add indices and vacuum cadence for doc_store (if enabled)
   - Indices on `content_hash`, `document_id`; periodic maintenance.
   - Outcome: faster queries, smaller DB.

8. Observability enhancements
   - Structured logs with levels; log-collector integration; health metrics.
   - Outcome: faster troubleshooting, better SLO tracking.

9. Golden tests for code-analyzer across common frameworks
   - Add Flask/Express samples; verify findings consistency.
   - Outcome: regression protection for analyzers.

10. Minimal CI security checks
    - Bandit (Python), Safety (deps); non-blocking initially.
    - Outcome: early detection of obvious security issues.

11. Testing consolidation and readability
    - Standardize test file naming and directories; add module docstrings and comments.
    - Introduce shared helpers (`tests/helpers`) and fixtures in `conftest.py`.
    - Use markers (`unit`, `integration`, `mocks`, `reports`, `orchestrator`, `security`).
    - Outcome: easier extension, faster onboarding, and clearer intent per test.

## Notes

- Keep scope constrained: no new external dependencies beyond lightweight middleware and existing tech.
- Prioritize changes that reduce variance, improve traceability, and increase resilience.


