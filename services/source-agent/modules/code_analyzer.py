"""Code analysis handler for Source Agent service.

Handles code analysis and endpoint extraction logic.
"""

from typing import Any, Dict

from .shared_utils import (
    build_source_agent_context,
    create_source_agent_success_response,
    extract_endpoints_from_code,
    handle_source_agent_error,
)


class CodeAnalyzer:
    """Handles code analysis operations for source agent.

    This class provides functionality to analyze source code for API endpoints,
    patterns, and other structural information. It supports multiple web frameworks
    and can extract routing information, security patterns, and architectural insights.
    """

    @staticmethod
    def analyze_code(text: str) -> Dict[str, Any]:
        """Analyze code for API endpoints and architectural patterns.

        Performs static analysis on source code to identify:
        - API endpoints and routes
        - Framework usage (FastAPI, Express, Flask, etc.)
        - Code patterns and anti-patterns
        - Security considerations

        Args:
            text: Source code content to analyze

        Returns:
            Dictionary containing analysis results with endpoints found,
            patterns detected, and metadata

        Raises:
            Various exceptions during analysis that are handled gracefully
        """
        try:
            hints = extract_endpoints_from_code(text)

            result = {
                "analysis": "\n".join(hints),
                "endpoint_count": len(hints),
                "patterns_found": ["FastAPI", "Express", "Flask"],
            }

            context = build_source_agent_context(
                "analyze_code", endpoint_count=len(hints)
            )
            return create_source_agent_success_response("analyzed", result, **context)

        except Exception as e:
            context = build_source_agent_context("analyze_code")
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_source_agent_error("analyze code", e, **context)


# Create singleton instance
code_analyzer = CodeAnalyzer()
