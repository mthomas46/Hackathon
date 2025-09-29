"""Test configuration for secure-analyzer service."""

import pytest
import sys
from pathlib import Path

# Add service path for imports
service_path = Path(__file__).parent
sys.path.insert(0, str(service_path))

# Add shared services path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))
