"""Validation logic for bedrock proxy service."""

from typing import Optional

from .templates import VALID_TEMPLATES, VALID_FORMATS
from .utils import sanitize_for_response


class ValidationError(ValueError):
    """Custom validation error for bedrock proxy."""
    pass


def validate_prompt(prompt: Optional[str]) -> Optional[str]:
    """Validate and sanitize prompt field."""
    if prompt is not None and not isinstance(prompt, str):
        raise ValidationError('Prompt must be a string')
    return prompt


def validate_template(template: Optional[str]) -> Optional[str]:
    """Validate template field."""
    if template is not None:
        valid_templates = VALID_TEMPLATES
        if template.lower() not in valid_templates and template.strip():
            raise ValidationError(f'Invalid template: {template}. Must be one of {valid_templates}')
    return template


def validate_format(fmt: Optional[str]) -> str:
    """Validate and normalize format field."""
    if fmt is not None:
        valid_formats = VALID_FORMATS
        if fmt.lower() not in valid_formats:
            raise ValidationError(f'Invalid format: {fmt}. Must be one of {valid_formats}')
    return (fmt or "md").lower()


def validate_model(model: Optional[str]) -> Optional[str]:
    """Validate and sanitize model field."""
    if model is not None:
        if len(model) > 100:
            raise ValidationError('Model name too long (max 100 characters)')
        # Sanitize dangerous content
        model = sanitize_for_response(model)
    return model


def validate_region(region: Optional[str]) -> Optional[str]:
    """Validate and sanitize region field."""
    if region is not None:
        if len(region) > 50:
            raise ValidationError('Region name too long (max 50 characters)')
        # Sanitize dangerous content
        region = sanitize_for_response(region)
    return region


def validate_title(title: Optional[str]) -> Optional[str]:
    """Validate title field."""
    if title is not None and len(title) > 200:
        raise ValidationError('Title too long (max 200 characters)')
    return title
