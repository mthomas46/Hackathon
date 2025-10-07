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
  - testing
  - monitoring
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

# ADR 0001: Standardized Envelopes for Responses

## Status
Accepted

## Context
Services returned heterogeneous response shapes. We want consistent clients, errors, and observability.

## Decision
Adopt success and error envelopes across services.

## Consequences
- Easier client consumption and testing
- Centralized error code taxonomy
- Slight overhead for wrapping responses
