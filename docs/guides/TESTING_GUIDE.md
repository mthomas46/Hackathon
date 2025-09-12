# Testing Guide

## Structure
- Tests live in `tests/unit/<service>`
- Common config and fixtures: `tests/conftest.py`

## Running tests
```bash
# All tests
pytest -q

# Specific service
pytest tests/unit/interpreter -q

# Verbose with short tracebacks
pytest -v --tb=short
```

## Useful markers and plugins
- Markers registered in `pytest.ini` and via `conftest.py` (unit, integration, slow, live, security, etc.)
- Plugins in use: `pytest-timeout`, `pytest-asyncio`, `pytest-xdist` (optional)

## Conventions
- Health checks: always assert `200` and expected JSON keys
- Envelope-aware tests: many endpoints return success envelopes; some return direct data
- Mocks: prefer lightweight async mocks and URL-based branching for service clients

## Examples
```bash
# Interpreter tests
pytest tests/unit/interpreter/test_interpreter_intents.py -q

# Log collector tests
pytest tests/unit/log_collector -q
```

## CI tips
- Ensure Python 3.11+ and install from `services/requirements.base.txt`
- Use `-q` in CI for concise output; add `-v` when diagnosing
