"""Validation logic for bedrock proxy service."""

from typing import Optional

from ..templates import VALID_FORMATS, VALID_TEMPLATES
from ..utils import sanitize_for_response


class ValidationError(ValueError):
    """Custom validation error for bedrock proxy."""


def validate_prompt(prompt: Optional[str]) -> Optional[str]:
    """Validate and sanitize prompt field."""
    if prompt is not None and not isinstance(prompt, str):
        raise ValidationError("Prompt must be a string")
    return prompt


def validate_template(template: Optional[str]) -> Optional[str]:
    """Validate template field."""
    if template is not None:
        valid_templates = VALID_TEMPLATES
        if template.lower() not in valid_templates and template.strip():
            raise ValidationError(
                f"Invalid template: {template}. Must be one of {valid_templates}"
            )
    return template


def validate_format(fmt: Optional[str]) -> str:
    """Validate and normalize format field."""
    if fmt is not None:
        valid_formats = VALID_FORMATS
        if fmt.lower() not in valid_formats:
            raise ValidationError(
                f"Invalid format: {fmt}. Must be one of {valid_formats}"
            )
    return (fmt or "md").lower()


def _validate_string_field(
    value: Optional[str],
    field_name: str,
    max_length: int,
    sanitize: bool = False
) -> Optional[str]:
    """Generic string field validation with common patterns."""
    if value is not None:
        if len(value) > max_length:
            raise ValidationError(f"{field_name} too long (max {max_length} characters)")
        if sanitize:
            value = sanitize_for_response(value)
    return value


def validate_model(model: Optional[str]) -> Optional[str]:
    """Validate and sanitize model field."""
    return _validate_string_field(model, "Model name", 100, sanitize=True)


def validate_region(region: Optional[str]) -> Optional[str]:
    """Validate and sanitize region field."""
    return _validate_string_field(region, "Region name", 50, sanitize=True)


def validate_title(title: Optional[str]) -> Optional[str]:
    """Validate title field."""
    return _validate_string_field(title, "Title", 200, sanitize=False)
