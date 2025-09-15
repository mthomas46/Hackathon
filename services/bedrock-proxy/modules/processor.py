"""Core processing logic for bedrock proxy service.

Handles the main request processing pipeline for AI invoke requests,
including input sanitization, template detection, and response formatting.
"""
from typing import Dict, Any, Optional

from .templates import (
    detect_template_from_prompt,
    generate_default_title,
    build_template_sections,
    render_markdown,
    render_text
)
from .utils import sanitize_for_response


def process_invoke_request(
    prompt: Optional[str] = None,
    template: Optional[str] = None,
    format: Optional[str] = None,
    title: Optional[str] = None,
    model: Optional[str] = None,
    region: Optional[str] = None,
    **kwargs  # Allow passthrough parameters
) -> Dict[str, Any]:
    """Process an AI invoke request and return a structured response.

    This function handles the complete pipeline for processing AI invoke requests:
    1. Input sanitization and validation
    2. Template auto-detection from prompt content
    3. Default title generation
    4. Structured content building
    5. Response formatting in requested format

    Args:
        prompt: Input text for AI processing
        template: Response template type (auto-detected if not provided)
        format: Output format ('md', 'txt', or 'json')
        title: Custom response title (auto-generated if not provided)
        model: AI model identifier for metadata
        region: AWS region for metadata
        **kwargs: Additional passthrough parameters

    Returns:
        Dict containing structured response with title, content, and metadata
    """
    # Normalize output format to lowercase with default
    output_format = (format or "md").lower()

    # Sanitize input prompt to prevent XSS attacks
    sanitized_prompt = sanitize_for_response(prompt or "").strip()

    # Auto-detect template from prompt content if not explicitly specified
    detected_template = template
    if not detected_template and sanitized_prompt:
        detected_template = detect_template_from_prompt(sanitized_prompt)

    # Normalize template to lowercase
    normalized_template = (detected_template or "").lower()

    # Generate default title if not provided
    response_title = title
    if not response_title:
        response_title = generate_default_title(normalized_template)

    # Sanitize title for safe response output
    sanitized_title = sanitize_for_response(response_title)

    # Build structured content sections based on template
    content_sections = build_template_sections(normalized_template, sanitized_prompt)

    # Sanitize model and region identifiers for response metadata
    safe_model = sanitize_for_response(model) if model else None
    safe_region = sanitize_for_response(region) if region else None

    # Return structured JSON response for JSON format requests
    if output_format == "json":
        return {
            "title": sanitized_title,
            "model": safe_model,
            "region": safe_region,
            "sections": content_sections,
        }

    # Render formatted text output for markdown or plain text
    formatted_body = (
        render_markdown(sanitized_title, content_sections)
        if output_format == "md"
        else render_text(sanitized_title, content_sections)
    )

    return {
        "output": formatted_body,
        "model": safe_model,
        "region": safe_region
    }
