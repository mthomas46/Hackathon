"""Test configuration and fixtures for architecture-digitizer tests."""

import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Mock the shared services import if not available
try:
    from services.shared.presentation.responses import APIResponse
except ImportError:
    # Create a simple mock APIResponse for testing
    from pydantic import BaseModel, Field
    from typing import Any, Dict, List, Optional
    from datetime import datetime, timezone

    class APIResponse(BaseModel):
        """Mock APIResponse for testing."""
        success: bool = Field(..., description="Whether the operation was successful")
        data: Optional[Any] = Field(None, description="Response data payload")
        message: Optional[str] = Field(None, description="Human-readable message")
        errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error details if applicable")
        request_id: Optional[str] = Field(None, description="Request correlation ID")
        timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(),
                              description="Response timestamp in ISO format")

        # Manually add dict() method for compatibility
        def dict(self):
            return self.model_dump()
