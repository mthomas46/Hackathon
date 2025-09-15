# Suggested Commands for LLM Documentation Ecosystem

## Development Setup
```bash
# Initial setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/requirements.base.txt

# Quick startup script
python start_services.py

# Start individual services
python services/orchestrator/main.py     # Port 5099
python services/doc-store/main.py        # Port 5087  
python services/source-agent/main.py     # Port 5000
```

## Testing
```bash
# Run all tests (fast)
pytest -q
make test

# Run specific service tests
pytest tests/unit/orchestrator/ -v
pytest tests/unit/interpreter/ -q

# Run with coverage
pytest --cov=services --cov-report=html

# Integration tests
pytest tests/integration/ -v --test-mode=integration
```

## Documentation
```bash
# Build docs
mkdocs build -q
make docs

# Serve docs locally
mkdocs serve -a 0.0.0.0:8000
make docs-serve
```

## Service Health Checks
```bash
# Check system health
curl http://localhost:5099/health/system

# Individual service health
curl http://localhost:5099/health
curl http://localhost:5087/health
curl http://localhost:5000/health
```

## Development Workflow
```bash
# Run tests before committing
pytest -q

# Check service endpoints
curl http://localhost:5099/info

# Start Redis (if needed for full functionality)
docker run -d -p 6379:6379 redis:7-alpine
```

## System Commands (Darwin/macOS)
- `ls`, `cd`, `grep`, `find` - standard Unix commands
- `git` - version control
- `docker` - containerization (optional for Redis)
- `curl` - API testing