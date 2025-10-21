---
llm_metadata:
  document_type: guide
  content_focus: technical
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - fastapi
  - python
  - testing
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about technical aspects of the shared platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# Test Suite Overview

## Layout
- `tests/unit/<service>` — unit/integration tests per service
- `tests/README.md` — extended testing framework docs (existing)

## Conventions
- Prefer success envelopes; handle direct-data responses when applicable
- Use `AsyncMock` for async HTTP clients; branch by URL
- Flexible assertions for order/accumulation in log-related tests
- FastAPI behavior: 422 for malformed JSON

## Running
```bash
pytest -q
pytest tests/unit/interpreter -q
pytest -v --tb=short
```

## CI
- Python 3.11+, dependencies from `services/requirements.base.txt`
- Optional xdist for parallelization
