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
