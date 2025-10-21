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
  - fastapi
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

# Errors and Envelopes

## Success envelope
```json
{
  "success": true,
  "data": { /* payload */ },
  "message": "optional",
  "request_id": "abc-123"
}
```

## Error envelope
```json
{
  "success": false,
  "error_code": "ANALYSIS_FAILED",
  "details": { /* context */ },
  "request_id": "abc-123"
}
```

## Common error codes
- ANALYSIS_FAILED
- REAPI_PORT_GENERATION_FAILED
- VALIDATION_ERROR
- SERVICE_UNAVAILABLE
- NATURAL_LANGUAGE_ANALYSIS_FAILED

## HTTP and FastAPI behavior
- 422 for malformed JSON at request parsing time
- 400 for explicit validation failures
- 5xx for server errors (surfaces with error envelope when handled)
