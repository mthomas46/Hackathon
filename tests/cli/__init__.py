"""
CLI Tests Package

This package contains comprehensive testing infrastructure for the Ecosystem CLI including:

- Unit tests for CLI command parsing and validation
- Integration tests for end-to-end CLI workflows
- Performance tests for CLI response times and resource usage
- Mock framework for testing without external dependencies
- Test fixtures for consistent test data
- Test runner for automated test execution

Modules:
- test_fixtures: Mock data and test fixtures
- mock_framework: Mock HTTP clients and Docker commands
- test_cli_unit: Unit tests for CLI functionality
- test_cli_integration: Integration tests for CLI workflows
- test_cli_performance: Performance tests for CLI operations
- test_runner: Automated test execution and reporting
"""

__version__ = "1.0.0"
__all__ = [
    "CLITestFixtures",
    "CLIMockFramework",
    "TestCLIUnit",
    "TestCLIIntegration",
    "TestCLIPerformance",
    "CLITestRunner"
]

# Import key classes for easy access
try:
    from .test_fixtures import CLITestFixtures
    from .mock_framework import CLIMockFramework
    from .test_cli_unit import TestCLIUnit
    from .test_cli_integration import TestCLIIntegration
    from .test_cli_performance import TestCLIPerformance
    from .test_runner import CLITestRunner
except ImportError:
    # Handle case where imports fail during testing
    pass
