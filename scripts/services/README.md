# Service Test Scripts

This directory contains test scripts for individual service validation and service-specific functionality.

## Test Categories

### Service Import Tests
- `test_services.py` - Validates that all services can import correctly after shared directory restructuring
- `test_services_direct.py` - Direct service module testing without full startup

### Service Runner Scripts
- `run_docstore.py` - Run Doc Store service
- `run_docstore_tests.py` - Run Doc Store-specific tests
- `run_orchestrator_standalone.py` - Run Orchestrator service standalone
- `run_promptstore.py` - Run Prompt Store service

### Test Data Scripts
- `populate_docstore_test_data.py` - Populate Doc Store with test data
- `populate_promptstore_test_data.py` - Populate Prompt Store with test data

### Interpreter Tests
- `test_interpreter_only.py` - Interpreter service-specific tests

## Test Scope

Service tests focus on:
- ✅ Service module imports and dependencies
- ✅ Service-specific configuration validation
- ✅ Individual service startup and basic functionality
- ✅ Service-specific business logic
- ✅ Database operations for individual services
- ✅ Service health endpoints

## What Service Tests DON'T Cover

Service tests do NOT test:
- ❌ CLI functionality (belongs in CLI tests)
- ❌ Cross-service communication (belongs in integration tests)
- ❌ Multi-service workflows (belongs in integration tests)
- ❌ Docker containerization (belongs in integration tests)

## Usage

```bash
# Test all service imports
python scripts/services/test_services.py

# Test specific service
python scripts/services/test_interpreter_only.py

# Populate test data
python scripts/services/populate_docstore_test_data.py
```

## Integration with Other Test Suites

Service tests provide the foundation for integration tests. They ensure individual services work correctly before testing cross-service interactions.
