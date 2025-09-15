# Task Completion Checklist

## Required Actions After Code Changes

### 1. Testing
```bash
# Always run tests before considering task complete
pytest -q

# Run specific service tests if changes are localized
pytest tests/unit/<service>/ -v

# For integration changes, run integration tests
pytest tests/integration/ -v --test-mode=integration
```

### 2. Code Quality
**Note**: No formal linting/formatting tools are configured in this project. Follow the code style conventions manually:
- Ensure descriptive naming and clear function signatures
- Add appropriate docstrings for non-trivial functions
- Use early returns and shallow nesting
- Follow project patterns for HTTP clients, envelopes, and middleware

### 3. Service Health Verification
```bash
# If you modified services, verify they start correctly
python services/<service>/main.py

# Check health endpoints
curl http://localhost:<port>/health
```

### 4. Documentation Updates
- Update relevant documentation in `docs/` if adding new features
- Update service README files if changing service behavior
- Update architecture documentation if changing service interactions

### 5. Integration Verification
```bash
# For changes affecting multiple services, verify system integration
python start_services.py
curl http://localhost:5099/health/system
```

## Service-Specific Considerations
- **Orchestrator changes**: Verify service registry functionality
- **Doc Store changes**: Test document storage and retrieval
- **Source Agent changes**: Test data ingestion workflows  
- **Analysis Service changes**: Verify analysis pipeline functionality
- **Frontend changes**: Test UI components and user interactions

## Git Workflow
- Ensure all tests pass before committing
- Follow conventional commit patterns
- Update CHANGELOG.md for significant changes