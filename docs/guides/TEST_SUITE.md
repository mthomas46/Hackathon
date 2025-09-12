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
