# CLI Test Scripts

This directory contains test scripts specifically for validating CLI functionality and user interface components.

## Test Categories

### CLI Functionality Tests
- `test_cli_simple.py` - Basic CLI command validation (help, commands, basic functionality)
- `test_cli_analysis_service.py` - Comprehensive Analysis Service CLI testing
- `test_cli_comprehensive.py` - Full CLI ecosystem testing with service integration
- `test_cli_interactive.py` - Interactive CLI testing scenarios

## Test Scope

CLI tests focus on:
- ✅ Command availability and help text
- ✅ Command execution without errors
- ✅ CLI menu system functionality
- ✅ Basic command validation
- ✅ CLI-specific error handling

## What CLI Tests DON'T Cover

CLI tests do NOT test:
- ❌ Service endpoint functionality (belongs in service tests)
- ❌ Cross-service integration (belongs in integration tests)
- ❌ Service-specific business logic (belongs in service tests)
- ❌ Database operations (belongs in service tests)

## Usage

```bash
# Test basic CLI functionality
python scripts/cli/test_cli_simple.py

# Test CLI with live services
python scripts/cli/test_cli_comprehensive.py --verbose

# Test interactive CLI scenarios
python scripts/cli/test_cli_interactive.py
```

## Test Results

Test results are saved to JSON files for analysis:
- `cli_simple_test_results.json`
- CLI test reports with detailed pass/fail metrics
