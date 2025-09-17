#!/usr/bin/env python3
"""Run Doc Store tests with proper path setup."""

import sys
import os
from pathlib import Path

# Setup Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment
os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('LOG_LEVEL', 'WARNING')

# Now run pytest
if __name__ == "__main__":
    import pytest
    import sys

    # Run the doc store tests
    sys.exit(pytest.main([
        "tests/unit/doc_store/",
        "-v",
        "--tb=short",
        "--cov=services.doc_store",
        "--cov-report=term-missing"
    ]))
