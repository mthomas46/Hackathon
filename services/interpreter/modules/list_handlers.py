"""List handlers for Interpreter service.

Handles the logic for list and info endpoints.
"""
from typing import Dict, Any

from .shared_utils import (
    get_supported_intents,
    create_interpreter_success_response,
    build_interpreter_context,
    handle_interpreter_error
)


class ListHandlers:
    """Handles list and info operations."""

    @staticmethod
    async def handle_list_supported_intents() -> Dict[str, Any]:
        """List all supported intents and examples."""
        try:
            intents_data = get_supported_intents()
            return create_interpreter_success_response(
                "intents retrieved",
                {"intents": intents_data},
                **build_interpreter_context("list_intents", intent_count=len(intents_data))
            )
        except Exception as e:
            return handle_interpreter_error(
                "list supported intents",
                e,
                **build_interpreter_context("list_intents_error")
            )


# Create singleton instance
list_handlers = ListHandlers()
