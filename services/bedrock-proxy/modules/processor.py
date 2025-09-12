"""Core processing logic for bedrock proxy service."""

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
    """Process an invoke request and return structured response."""

    # Normalize format to lowercase
    fmt = (format or "md").lower()

    # Sanitize the prompt to prevent XSS attacks
    text = sanitize_for_response(prompt or "").strip()

    # Auto-detect template if not explicitly provided
    if not template and text:
        template = detect_template_from_prompt(text)

    # Normalize template to lowercase
    template = (template or "").lower()

    # Generate title if not provided
    if not title:
        title = generate_default_title(template)

    # Sanitize title for response
    title = sanitize_for_response(title)

    # Build structured content
    sections = build_template_sections(template, text)

    # Sanitize model and region for response
    safe_model = sanitize_for_response(model) if model else None
    safe_region = sanitize_for_response(region) if region else None

    if fmt == "json":
        return {
            "title": title,
            "model": safe_model,
            "region": safe_region,
            "sections": sections,
        }

    # Render formatted output
    body = render_markdown(title, sections) if fmt == "md" else render_text(title, sections)
    return {
        "output": body,
        "model": safe_model,
        "region": safe_region
    }
