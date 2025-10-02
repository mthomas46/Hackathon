# CLI Test Scripts

This directory contains consolidated test scripts for validating CLI functionality and user interface components.

## Scripts

### `test_cli_consolidated.py`
**Comprehensive CLI Testing Suite** - Unified testing framework for validating all CLI functionality and user interface components.

**Features:**
- Complete CLI command validation across all modules
- Interactive CLI testing scenarios with automated workflows
- Error handling and edge case validation
- Live service integration testing capabilities
- Performance benchmarking for CLI operations
- Automated regression testing for CLI changes
- Comprehensive test reporting with detailed metrics

**Use Cases:**
- CLI development and feature validation
- User experience testing and optimization
- Performance bottleneck identification
- Automated testing in CI/CD pipelines
- Regression testing after CLI updates
- Quality assurance for CLI releases

### `run_cli.py`
**CLI Runner and Launcher** - Simple script for launching the main CLI application with proper environment setup.

**Features:**
- Environment variable configuration
- Python path setup for proper imports
- Error handling for CLI startup issues
- Logging configuration for debugging
- Development environment optimization

**Use Cases:**
- Quick CLI testing during development
- Automated CLI execution in scripts
- Environment setup validation
- Debugging CLI startup issues
- Development workflow integration

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
