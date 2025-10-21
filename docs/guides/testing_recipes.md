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

# Testing Recipes

## Async HTTP client mocking
```python
from unittest.mock import AsyncMock

async def mock_get_json(url, **kwargs):
    if url.endswith("/health"):
        return {"status": "healthy"}
    if url.startswith("prompt-store/prompts"):
        return {"prompts": [{"category": "summary", "name": "basic"}]}
    raise Exception(f"Unexpected GET URL: {url}")

mock_clients.get_json = AsyncMock(side_effect=mock_get_json)
```

## Envelope-aware assertions
```python
resp = client.get("/intents")
assert resp.status_code == 200
body = resp.json()
if "success" in body:
    assert body["success"] is True
    assert "data" in body
```

## Flexible result structures
```python
# Some workflow steps may return dicts or strings
for result in results:
    if isinstance(result, dict):
        assert "content" in result or "status" in result
    elif isinstance(result, str):
        assert result
```

## Handling 422 vs 400
- FastAPI returns 422 for malformed JSON parsing
- Services may return 400 for domain validation errors
