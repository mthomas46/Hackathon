"""Shared utilities for Prompt Store service modules.

This module contains common utilities used across all prompt-store modules
to eliminate code duplication and ensure consistency.
"""

import os
from typing import Dict, Any, Optional
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException
from services.shared.constants_new import ErrorCodes, ServiceNames
from services.shared.logging import fire_and_forget
# Import database - handle both relative and absolute imports for different loading contexts
try:
    from .database import PromptStoreDatabase
except ImportError:
    try:
        from ..database import PromptStoreDatabase
    except ImportError:
        # Fallback for when loaded via importlib
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from database import PromptStoreDatabase

# Global database instance for shared access
_db = None

def get_prompt_store_client():
    """Get or create database instance for prompt store.

    Uses lazy initialization pattern to ensure single database connection
    across all prompt store modules.
    """
    global _db
    if _db is None:
        # Use absolute path to ensure it works regardless of current working directory
        default_db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "prompt_store.db")
        db_path = os.environ.get("PROMPT_STORE_DB", default_db_path)
        _db = PromptStoreDatabase(db_path)
    return _db


def handle_prompt_error(operation_name: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for prompt operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget("error", f"Prompt {operation_name} error: {error}", ServiceNames.PROMPT_STORE, context)
    return create_error_response(
        f"Failed to {operation_name} prompt",
        error_code=ErrorCodes.DATABASE_ERROR,
        details={"error": str(error), **context}
    )


def create_prompt_success_response(operation_name: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for prompt operations.

    Returns a consistent success response format.
    """
    return create_success_response(f"Prompt {operation_name} successful", data, **context)


def build_prompt_context(operation: str, prompt_id: Optional[str] = None, category: Optional[str] = None, **additional) -> Dict[str, Any]:
    """Build context dictionary for prompt operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "operation": operation,
        "service": "prompt-store"
    }

    if prompt_id:
        context["prompt_id"] = prompt_id
    if category:
        context["category"] = category

    context.update(additional)
    return context


def validate_prompt_data(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate prompt data before processing.

    Performs basic validation on prompt fields and returns
    cleaned/validated data.
    """
    if not prompt_data.get('name'):
        raise ServiceException(
            "Prompt name is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"field": "name"}
        )

    if not prompt_data.get('category'):
        raise ServiceException(
            "Prompt category is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"field": "category"}
        )

    if not prompt_data.get('content'):
        raise ServiceException(
            "Prompt content is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"field": "content"}
        )

    # Ensure variables is a list
    if 'variables' in prompt_data and not isinstance(prompt_data['variables'], list):
        prompt_data['variables'] = []

    # Ensure tags is a list
    if 'tags' in prompt_data and not isinstance(prompt_data['tags'], list):
        prompt_data['tags'] = []

    return prompt_data


def extract_prompt_variables(content: str) -> list:
    """Extract template variables from prompt content.

    Uses regex to find all {variable_name} patterns in the content.
    """
    import re
    variables = set()
    pattern = r'\{([^}]+)\}'

    matches = re.findall(pattern, content)
    for match in matches:
        variables.add(match)

    return list(variables)
