"""Shared DTO Validators

Common validation patterns used across all DTOs to reduce duplication
and ensure consistency.
"""

from pydantic import field_validator


class CommonValidators:
    """Common validation methods for DTOs."""

    @staticmethod
    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v):
        """Validate that name is not empty after stripping whitespace."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @staticmethod
    @field_validator('description')
    @classmethod
    def validate_description_length(cls, v):
        """Validate description length."""
        if v and len(v) > 1000:
            raise ValueError('Description too long (max 1000 characters)')
        return v

    @staticmethod
    @field_validator('tags')
    @classmethod
    def validate_tags_format(cls, v):
        """Validate tags are strings and not too many."""
        if not isinstance(v, list):
            raise ValueError('Tags must be a list')
        if len(v) > 50:
            raise ValueError('Too many tags (max 50)')
        for tag in v:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError('Tags must be non-empty strings')
            if len(tag) > 100:
                raise ValueError('Tag too long (max 100 characters)')
        return [tag.strip() for tag in v]

    @staticmethod
    @field_validator('service_name', 'workflow_type', 'report_type')
    @classmethod
    def validate_identifier_not_empty(cls, v):
        """Validate identifiers are not empty."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError('Identifier cannot be empty')
        return v.strip()

    @staticmethod
    @field_validator('url', 'base_url', 'openapi_url')
    @classmethod
    def validate_url_format(cls, v):
        """Basic URL format validation."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
