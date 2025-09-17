# Validation Scripts

This directory contains scripts for validating service compliance, API compatibility, and system health.

## Test Categories

### API Compatibility Tests
- `test_api_compatibility.py` - Validates backward compatibility for all 53 Analysis Service endpoints
- `test_all_endpoints.py` - Comprehensive endpoint testing with performance metrics

### Service Validation Tests
- `test_service_imports.py` - Validates service module imports and dependencies
- `validate_test_structure.py` - Validates test suite structure and coverage

### Performance and Health Tests
- `code_complexity_analysis.py` - Code complexity analysis and metrics
- `memory_analysis.py` - Memory usage analysis and leak detection
- `performance_benchmark.py` - Performance benchmarking and optimization

## Test Scope

Validation scripts focus on:
- ✅ API backward compatibility and contract validation
- ✅ Service import validation and dependency checking
- ✅ Code quality and complexity metrics
- ✅ Performance benchmarking and optimization
- ✅ Memory usage analysis and leak detection
- ✅ Compliance with coding standards and best practices

## What Validation Tests DON'T Cover

Validation tests do NOT test:
- ❌ Functional business logic (belongs in service tests)
- ❌ Cross-service integration (belongs in integration tests)
- ❌ CLI functionality (belongs in CLI tests)
- ❌ User interface testing (belongs in CLI tests)

## Usage

```bash
# Validate API compatibility
python scripts/validation/test_api_compatibility.py

# Test all endpoints
python scripts/validation/test_all_endpoints.py

# Validate service imports
python scripts/validation/test_service_imports.py

# Performance benchmarking
python scripts/validation/performance_benchmark.py
```

## Compliance and Standards

Validation scripts ensure compliance with:
- API contract specifications
- Backward compatibility requirements
- Code quality standards
- Performance benchmarks
- Memory usage limits
- Security best practices

## Integration with CI/CD

These validation scripts are designed to be run in CI/CD pipelines to:
- Catch compatibility regressions
- Validate performance requirements
- Ensure code quality standards
- Provide compliance reporting
