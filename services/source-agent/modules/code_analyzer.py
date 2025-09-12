"""Code analysis handler for Source Agent service.

Handles code analysis and endpoint extraction logic.
"""
from typing import Dict, Any, List

from .shared_utils import (
    extract_endpoints_from_code,
    create_source_agent_success_response,
    build_source_agent_context,
    handle_source_agent_error
)


class CodeAnalyzer:
    """Handles code analysis operations."""

    @staticmethod
    def analyze_code(text: str) -> Dict[str, Any]:
        """Analyze code for API endpoints and patterns."""
        try:
            hints = extract_endpoints_from_code(text)

            result = {
                "analysis": "\n".join(hints),
                "endpoint_count": len(hints),
                "patterns_found": ["FastAPI", "Express", "Flask"]
            }

            context = build_source_agent_context("analyze_code", endpoint_count=len(hints))
            return create_source_agent_success_response("analyzed", result, **context)

        except Exception as e:
            context = build_source_agent_context("analyze_code")
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_source_agent_error("analyze code", e, **context)


# Create singleton instance
code_analyzer = CodeAnalyzer()
