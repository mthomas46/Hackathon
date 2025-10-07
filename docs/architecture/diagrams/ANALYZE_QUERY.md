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

# Analyze Query Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI/Frontend as CLI / Frontend
    participant Interpreter
    participant Orchestrator
    participant Analysis as Analysis Service
    participant DocStore as Doc Store

    User->>CLI/Frontend: Enter natural language request
    CLI/Frontend->>Interpreter: POST /interpret {query}
    Interpreter-->>CLI/Frontend: {intent, entities, workflow}
    alt workflow present
      CLI/Frontend->>Interpreter: POST /execute {query}
      Interpreter->>Analysis: (steps) analyze/findings
      Analysis->>DocStore: store results
      Analysis-->>Interpreter: findings summary
      Interpreter-->>CLI/Frontend: {status: completed, results}
    else no workflow
      Interpreter-->>CLI/Frontend: {status: no_workflow}
    end
```

## Components
```mermaid
graph TD
  UI[CLI/Frontend]
  INT[Interpreter]
  ANA[Analysis Service]
  DS[Doc Store]
  ORCH[Orchestrator]

  UI --> INT
  INT --> ANA
  ANA --> DS
  INT -.optional.-> ORCH
```
