# Scripts Directory

This directory contains various scripts for development, testing, demonstration, and operations of the LLM Documentation Ecosystem.

## Directory Structure

### Core Scripts
- `run_*.py` - Service runner scripts for development and testing
- `start_services.py` - Script to start all services in development mode
- `init_docstore_db.py` - Database initialization for Doc Store
- `populate_*_test_data.py` - Test data population scripts
- `run_sanity_tests.py` - Basic sanity checks for services

### Demo Scripts (`demo/`)
- `demo_refactored_architecture.py` - Demonstration of refactored architecture
- `demo_workflow_management.py` - Workflow management demonstrations

### Test Scripts (`test/`)
- `test_services.py` - Comprehensive service import testing
- `test_services_direct.py` - Direct service testing script
- `service_test_results.txt` - Results from service testing
- Various `test_*.py` files - Individual component tests

### Verification Scripts (`verification/`)
- `enterprise_features_verification.py` - Enterprise feature verification
- `enterprise_integration_verification.py` - Integration testing
- `service_audit_simplified.py` - Simplified service auditing
- `verify_enterprise_integration.py` - Enterprise integration verification

### Benchmarking and Analysis
- `benchmark_prompt_store.py` - Performance benchmarking for Prompt Store
- `generate_timeline.py` - Timeline generation for project tracking

## Usage

### Running Services
```bash
# Start all services
python scripts/start_services.py

# Start individual services
python scripts/run_docstore.py
python scripts/run_orchestrator_standalone.py
```

### Testing
```bash
# Run comprehensive service tests
python scripts/test/test_services_direct.py

# Run individual tests
python scripts/test/test_enterprise_error_handling.py
```

### Demonstrations
```bash
# Run architecture demo
python scripts/demo/demo_refactored_architecture.py

# Run workflow demo
python scripts/demo/demo_workflow_management.py
```

## Contributing

When adding new scripts:

1. Place scripts in the appropriate subdirectory
2. Add clear documentation and usage examples
3. Include error handling and logging
4. Update this README with the new script information
5. Test the script in the appropriate environment

## Maintenance

- Clean up old/unused scripts regularly
- Keep scripts well-documented
- Ensure scripts handle errors gracefully
- Update dependencies as needed
