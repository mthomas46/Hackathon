---
llm_metadata:
  document_type: architecture
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
  semantic_summary: Architecture document about technical aspects of the shared platform
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

# ADR 0002: Policy Enforcement for Summarization

## Status
Accepted

## Context
We must restrict providers when content is sensitive; allow broader access when not.

## Decision
Secure Analyzer enforces provider selection based on detection. Override via `override_policy` when explicitly allowed.

## Consequences
- Safer defaults for regulated content
- Clear separation of detection vs policy enforcement
- Requires tests and docs to reflect policy
