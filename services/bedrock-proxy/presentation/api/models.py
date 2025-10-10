"""API request/response models for Bedrock Proxy.

This module contains Pydantic models for API endpoints, including validation logic.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator


class InvokeRequest(BaseModel):
    """Request model for AI invoke endpoint.
    
    Supports template-driven responses with multiple output formats.
    """
    
    model: Optional[str] = None
    """AWS Bedrock model identifier (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')."""
    
    region: Optional[str] = None
    """AWS region for model deployment (e.g., 'us-east-1')."""
    
    prompt: Optional[str] = None
    """Input prompt text for AI processing."""
    
    params: Optional[Dict[str, Any]] = None
    """Additional parameters to pass through to the AI model."""
    
    template: Optional[str] = None
    """Response template type: summary|risks|decisions|pr_confidence|life_of_ticket"""
    
    style: Optional[str] = None
    """Output style format: bullet|paragraph (currently unused)."""
    
    format: Optional[str] = "md"
    """Output format: md|txt|json"""
    
    title: Optional[str] = None
    """Custom title for the generated response."""
    
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v):
        """Validate that prompt is a string if provided."""
        if v is not None and not isinstance(v, str):
            raise ValueError("Prompt must be a string value")
        return v
    
    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        """Validate template is one of the supported types."""
        if v is not None:
            valid_templates = [
                "summary", "risks", "decisions",
                "pr_confidence", "life_of_ticket",
            ]
            if v.lower() not in valid_templates and v.strip():
                raise ValueError(
                    f'Invalid template "{v}". Supported templates: {", ".join(valid_templates)}'
                )
        return v
    
    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        """Validate output format is supported."""
        if v is not None:
            valid_formats = ["md", "txt", "json"]
            if v.lower() not in valid_formats:
                raise ValueError(
                    f'Invalid format "{v}". Supported formats: {", ".join(valid_formats)}'
                )
        return (v or "md").lower()
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model name length."""
        if v is not None and len(v) > 100:
            raise ValueError("Model name exceeds maximum length of 100 characters")
        return v
    
    @field_validator("region")
    @classmethod
    def validate_region(cls, v):
        """Validate region name length."""
        if v is not None and len(v) > 50:
            raise ValueError("Region name exceeds maximum length of 50 characters")
        return v
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate title length."""
        if v is not None and len(v) > 200:
            raise ValueError("Title exceeds maximum length of 200 characters")
        return v

