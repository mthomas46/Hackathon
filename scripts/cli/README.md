# CLI Test Scripts

This directory contains consolidated test scripts for validating CLI functionality and user interface components.

## Consolidated Test Suite

### `test_cli_consolidated.py`
**Comprehensive CLI Testing** - Combines all previous CLI test functionality:
- Basic CLI command validation (help, commands, basic functionality)
- CLI ecosystem testing with service integration
- Interactive CLI testing scenarios
- Error handling and edge case testing
- Live service integration testing

## Test Scope

CLI tests focus on:
- ✅ Command availability and help text
- ✅ Command execution without errors
- ✅ CLI menu system functionality
- ✅ Basic command validation
- ✅ CLI-specific error handling
- ✅ Interactive features and help systems
- ✅ Integration with live services (when available)

## What CLI Tests DON'T Cover

CLI tests do NOT test:
- ❌ Service endpoint functionality (belongs in service tests)
- ❌ Cross-service integration (belongs in integration tests)
- ❌ Service-specific business logic (belongs in service tests)
- ❌ Database operations (belongs in service tests)

## Usage

```bash
# Run comprehensive CLI testing
python scripts/cli/test_cli_consolidated.py

# Test results are saved to cli_simple_test_results.json
```

## Test Categories

The consolidated test suite includes:

1. **Basic CLI Functionality**
   - Help command validation
   - Command listing and availability
   - Health command testing

2. **CLI Feature Testing**
   - Document analysis commands
   - Code analysis commands
   - Prompt management commands

3. **Error Handling**
   - Invalid command handling
   - Missing argument handling
   - Graceful failure testing

4. **Interactive Features**
   - Help system validation
   - Command assistance
   - User interface elements

5. **Live Service Integration** (Optional)
   - Tests CLI commands against running services
   - Service availability checking
   - Real-world usage scenarios

## Test Results

Test results are saved to `cli_simple_test_results.json` with detailed pass/fail metrics and performance data.
