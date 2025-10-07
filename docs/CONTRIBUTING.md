---
llm_metadata:
  document_type: reference
  content_focus: technical
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Reference document about technical aspects of the shared platform
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

# Contributing

## Workflow
- Create feature branches from main
- Write tests and update docs for any behavioral change
- Ensure `pytest -q` passes locally

## Commit style
- Conventional-ish: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

## PR checklist
- [ ] Tests added/updated
- [ ] Service README updated if API/behavior changes
- [ ] Docs site builds locally (mkdocs)

## Local tasks
```bash
make test   # run tests
make docs   # build docs site locally
```
