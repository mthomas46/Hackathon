"""Shared utilities for Interpreter service modules.

This module contains common utilities used across all interpreter modules
to eliminate code duplication and ensure consistency.
"""

import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Import shared utilities
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.error_handling import ServiceException, ValidationException
from services.shared.responses import create_success_response, create_error_response
from services.shared.logging import fire_and_forget
from services.shared.utilities import utc_now, generate_id

# Global configuration for interpreter service
_DEFAULT_TIMEOUT = 30
_INTERPRETER_PORT = int(os.environ.get("INTERPRETER_PORT", "5120"))

def get_default_timeout() -> int:
    """Get default service client timeout."""
    return _DEFAULT_TIMEOUT

def get_interpreter_port() -> int:
    """Get interpreter service port from environment."""
    return _INTERPRETER_PORT

def get_interpreter_clients(timeout: int = _DEFAULT_TIMEOUT) -> ServiceClients:
    """Create and return a ServiceClients instance with proper timeout."""
    return ServiceClients(timeout=timeout)

def handle_interpreter_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for interpreter operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget("error", f"Interpreter {operation} error: {error}", ServiceNames.INTERPRETER, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.INTERNAL_ERROR,
        details={"error": str(error), **context}
    )

def create_interpreter_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for interpreter operations.

    Returns a consistent success response format.
    """
    return create_success_response(f"Interpreter {operation} successful", data, **context)

def build_interpreter_context(operation: str, **additional) -> Dict[str, Any]:
    """Build context dictionary for interpreter operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "operation": operation,
        "service": ServiceNames.INTERPRETER
    }
    context.update(additional)
    return context

def validate_user_query(query: Dict[str, Any]) -> None:
    """Validate user query parameters."""
    if not query.get("query"):
        raise ValidationException(
            "Query text is required",
            {"query": ["Required field - cannot be empty"]}
        )

    query_text = query["query"].strip()
    if len(query_text) < 3:
        raise ValidationException(
            "Query too short",
            {"query": ["Must be at least 3 characters long"]}
        )

    if len(query_text) > 1000:
        raise ValidationException(
            "Query too long",
            {"query": ["Must be less than 1000 characters"]}
        )

def extract_entities_with_pattern(query: str, pattern: str) -> List[str]:
    """Extract entities from query using regex pattern."""
    if not query or not pattern:
        return []

    matches = re.findall(pattern, query, re.IGNORECASE)
    return list(set(matches)) if matches else []

def add_entity_if_found(entities: Dict[str, Any], entity_list: List[str], key: str) -> None:
    """Add entity to entities dict if found."""
    if entity_list:
        entities[key] = entity_list

def build_workflow_response(intent: str, confidence: float, entities: Dict[str, Any], workflow: Optional[Any] = None) -> Dict[str, Any]:
    """Build standardized workflow response."""
    response = {
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "timestamp": utc_now().isoformat()
    }

    if workflow:
        response["workflow"] = workflow

    return response

def generate_response_text(intent: str, confidence: float, entities: Dict[str, Any], workflow: Optional[Any]) -> str:
    """Generate human-readable response text based on interpretation."""
    if confidence < 0.3:
        return "I'm not sure what you're asking for. Could you please rephrase your request?"

    if intent == "analyze_document":
        urls = entities.get("urls", [])
        if urls:
            return f"I'll analyze the document(s) from: {', '.join(urls)}"
        else:
            return "I'll analyze your documents for consistency and issues."

    elif intent.startswith("ingest_"):
        source_type = intent.replace("ingest_", "")
        return f"I'll ingest data from {source_type} for you."

    elif intent == "create_prompt":
        return "I'll help you create a new prompt. What would you like it to do?"

    elif intent == "find_prompt":
        search_terms = entities.get("search_terms", [])
        if search_terms:
            return f"I'll search for prompts related to: {', '.join(search_terms)}"
        else:
            return "I'll search for prompts matching your criteria."

    elif intent == "generate_report":
        return "I'll generate a comprehensive report for you."

    elif intent == "help":
        return ("I can help you with:\n"
                "• Document analysis and consistency checking\n"
                "• Data ingestion from GitHub, Jira, and Confluence\n"
                "• Prompt management and creation\n"
                "• Report generation\n"
                "• System status and analytics\n\n"
                "Just tell me what you'd like to do!")

    elif intent == "status":
        return "Let me check the system status for you."

    else:
        return f"I understand you want to {intent.replace('_', ' ')}. Let me help you with that."

def calculate_intent_confidence(query: str, pattern: str, intent: str) -> float:
    """Calculate confidence score for intent recognition."""
    if not query or not pattern:
        return 0.0

    query_lower = query.lower()
    if re.search(pattern, query_lower, re.IGNORECASE):
        # Base confidence on pattern complexity and match quality
        pattern_words = len(pattern.split())
        query_words = len(query.split())

        if pattern_words > 2:
            base_confidence = 0.8
        else:
            base_confidence = 0.6

        # Boost confidence for exact matches
        if pattern.lower() in query_lower:
            base_confidence += 0.1

        # Reduce confidence for very short queries
        if query_words < 3:
            base_confidence *= 0.8

        return min(base_confidence, 1.0)

    return 0.0

def normalize_entity_matches(matches: List[str], entity_type: str) -> List[str]:
    """Normalize entity matches based on type."""
    if not matches:
        return matches

    if entity_type == "repo":
        # Special handling for GitHub repo patterns
        normalized = []
        for match in matches:
            if isinstance(match, tuple) and len(match) >= 2:
                normalized.append(f"{match[0]}/{match[1]}")
            elif "/" in match:
                normalized.append(match)
        return normalized

    elif entity_type == "url":
        # Clean up URLs
        normalized = []
        for match in matches:
            match = match.strip(".,;()[]{}")
            if match.startswith(("http://", "https://")):
                normalized.append(match)
        return normalized

    elif entity_type == "email":
        # Basic email normalization
        return [match.lower() for match in matches]

    else:
        return list(set(matches))  # Remove duplicates for other types

def create_workflow_id(prefix: str) -> str:
    """Create a unique workflow ID."""
    timestamp = utc_now().strftime('%Y%m%d_%H%M%S')
    unique_id = generate_id()[:8]
    return f"{prefix}_{timestamp}_{unique_id}"

def validate_workflow_step(step: Dict[str, Any]) -> None:
    """Validate workflow step structure."""
    required_fields = ["step_id", "service", "action", "parameters"]

    for field in required_fields:
        if field not in step:
            raise ValidationException(
                f"Workflow step missing required field: {field}",
                {"step": [f"Missing {field}"], "required_fields": required_fields}
            )

    if not step.get("step_id"):
        raise ValidationException(
            "Workflow step ID cannot be empty",
            {"step_id": ["Cannot be empty"]}
        )

    if not step.get("service"):
        raise ValidationException(
            "Workflow step service cannot be empty",
            {"service": ["Cannot be empty"]}
        )

def get_supported_intents() -> Dict[str, Dict[str, Any]]:
    """Get comprehensive list of supported intents with examples."""
    return {
        "analyze_document": {
            "description": "Analyze documents for consistency, quality, and security issues",
            "examples": [
                "analyze this document for issues",
                "check the consistency of my files",
                "review this content for problems",
                "scan document for security vulnerabilities"
            ],
            "confidence_threshold": 0.7
        },

        "consistency_check": {
            "description": "Run comprehensive consistency validation across documents",
            "examples": [
                "check consistency across all documents",
                "find inconsistencies in the documentation",
                "validate consistency of the system",
                "run consistency analysis"
            ],
            "confidence_threshold": 0.8
        },

        "ingest_github": {
            "description": "Ingest data from GitHub repositories",
            "examples": [
                "ingest from github repository",
                "pull documentation from github",
                "import github repo content",
                "sync with github project"
            ],
            "confidence_threshold": 0.8
        },

        "ingest_jira": {
            "description": "Ingest data from Jira tickets and projects",
            "examples": [
                "ingest jira tickets",
                "pull from jira project",
                "import jira issues",
                "sync jira data"
            ],
            "confidence_threshold": 0.8
        },

        "ingest_confluence": {
            "description": "Ingest data from Confluence pages and spaces",
            "examples": [
                "ingest confluence pages",
                "pull from confluence space",
                "import confluence documentation",
                "sync confluence content"
            ],
            "confidence_threshold": 0.8
        },

        "create_prompt": {
            "description": "Create new prompts for AI operations",
            "examples": [
                "create a new prompt",
                "make a prompt for analysis",
                "add a custom prompt",
                "design a new prompt template"
            ],
            "confidence_threshold": 0.7
        },

        "find_prompt": {
            "description": "Search for existing prompts",
            "examples": [
                "find prompts about security",
                "search for analysis prompts",
                "get prompts for documentation",
                "show me available prompts"
            ],
            "confidence_threshold": 0.7
        },

        "generate_report": {
            "description": "Generate comprehensive reports",
            "examples": [
                "generate a system report",
                "create analysis report",
                "make documentation report",
                "run comprehensive report"
            ],
            "confidence_threshold": 0.8
        },

        "help": {
            "description": "Get help and information about capabilities",
            "examples": [
                "help me",
                "what can you do",
                "show commands",
                "list available features"
            ],
            "confidence_threshold": 0.9
        },

        "status": {
            "description": "Check system status and health",
            "examples": [
                "show status",
                "system status",
                "health check",
                "how are you doing"
            ],
            "confidence_threshold": 0.8
        }
    }

def log_interpretation_metrics(query: str, intent: str, confidence: float, processing_time: float) -> None:
    """Log interpretation metrics for monitoring."""
    context = {
        "query_length": len(query),
        "intent": intent,
        "confidence": confidence,
        "processing_time_ms": processing_time * 1000,
        "service": ServiceNames.INTERPRETER
    }
    fire_and_forget("info", "Query interpretation completed", ServiceNames.INTERPRETER, context)
