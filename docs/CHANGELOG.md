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
  - testing
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

# Changelog

## Unreleased
- **CLI Service Major Refactoring**: Mixin-based architecture, 18+ standardized managers, 100% test improvement (72→153 tests)
- Add comprehensive service READMEs with endpoint/env/testing sections
- Add docs site scaffolding (mkdocs)
- Add Errors & Envelopes and Testing Recipes
- Add Docs Parity Matrix
