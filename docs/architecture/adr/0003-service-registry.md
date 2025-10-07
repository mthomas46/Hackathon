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
  topics: []
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

# ADR 0003: Orchestrator Service Registry

## Status
Accepted

## Context
Services need to discover each other with minimal configuration and support peer replication.

## Decision
Orchestrator provides a registry with self-registration endpoints and peer replication.

## Consequences
- Simplifies service discovery in dev/test
- Supports eventual consistency via peer sync
- Requires health checks to prune stale entries
