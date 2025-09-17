# Scripts Directory Organization

This directory contains all scripts for the LLM Documentation Ecosystem, organized by purpose and functionality.

## Directory Structure

```
scripts/
├── startup/          # Service startup and management scripts
├── services/         # Service-specific test and utility scripts
├── cli/             # CLI-specific test scripts
├── integration/     # Cross-service integration test scripts
├── validation/      # Compliance and validation scripts
├── demo/            # Demonstration and showcase scripts
├── docs/            # Documentation generation scripts
├── migration/       # Database migration scripts
└── README.md        # This file
```

## Script Categories

### 🚀 Startup Scripts (`startup/`)
Scripts for starting and managing services locally
- Individual service starters (13 services)
- Master startup script for all services
- Service dependency management
- Health monitoring

### 🔧 Service Scripts (`services/`)
Service-specific testing and utility scripts
- Service import validation
- Service-specific tests
- Test data population
- Service runner scripts

### 💻 CLI Scripts (`cli/`)
CLI-specific testing and validation
- CLI functionality tests
- Command validation
- Interactive testing
- CLI performance validation

### 🔗 Integration Scripts (`integration/`)
Cross-service integration testing
- Docker integration testing
- Service mesh validation
- Workflow orchestration testing
- End-to-end integration tests

### ✅ Validation Scripts (`validation/`)
Compliance and quality validation
- API compatibility testing
- Code quality analysis
- Performance benchmarking
- Memory usage analysis

### 🎬 Demo Scripts (`demo/`)
Demonstration and showcase scripts
- System capability demonstrations
- Interactive workflow examples
- Architecture showcase
- User experience examples

### 📚 Documentation Scripts (`docs/`)
Documentation generation and management
- Timeline generation
- Status reporting
- Documentation updates

### 🔄 Migration Scripts (`migration/`)
Database migration and data transformation
- Schema migration scripts
- Data transformation utilities
- Backward compatibility handling

## Test Suite Organization

The test suites are organized by scope to avoid overlap:

1. **Service Tests** (`services/`) - Individual service functionality
2. **Integration Tests** (`integration/`) - Cross-service interactions
3. **CLI Tests** (`cli/`) - User interface and CLI functionality
4. **Validation Tests** (`validation/`) - Compliance and quality checks

## Quick Start

```bash
# Start all services locally
python scripts/startup/start_all_services.py --start

# Run service tests
python scripts/services/test_services.py

# Test CLI functionality
python scripts/cli/test_cli_simple.py

# Run integration tests
python scripts/integration/test_full_integration.py

# Validate system
python scripts/validation/test_api_compatibility.py
```

## Best Practices

### Script Organization
- Keep scripts focused on single responsibilities
- Include comprehensive error handling
- Provide clear usage documentation
- Include cleanup procedures

### Test Script Guidelines
- Service tests should not test integration
- Integration tests should not test CLI functionality
- CLI tests should focus on user interface
- Validation tests should focus on compliance

### Naming Conventions
- Use descriptive names with clear purpose
- Include test type in filename (test_*, validate_*, demo_*)
- Use consistent prefixes for related scripts

## Maintenance

### Adding New Scripts
1. Determine appropriate category/subdirectory
2. Follow naming conventions
3. Update relevant README files
4. Test script functionality
5. Update main README if needed

### Updating Existing Scripts
1. Maintain backward compatibility
2. Update documentation
3. Test thoroughly before committing
4. Update README files as needed