"""End-to-end tests for MCP ecosystem.

These tests can run in two modes:
1. Code Mode: Tests against service code with mocked dependencies (CI/CD)
2. Live Mode: Tests against running Docker containers (staging/production)

Set TEST_MODE environment variable to control mode:
    export TEST_MODE=code  # For CI/CD
    export TEST_MODE=live  # For staging/production validation
"""

__version__ = "1.0.0"