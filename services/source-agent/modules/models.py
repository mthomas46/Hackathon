"""Request and response models for Source Agent service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator


class DocumentRequest(BaseModel):
    """Request model for document fetching."""
    source: str  # github, jira, confluence
    identifier: str  # repo path, issue key, page ID
    scope: Optional[dict] = None

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        supported = ['github', 'jira', 'confluence']
        if v not in supported:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'source_not_supported',
                'Unsupported source: {source}. Must be one of {supported}',
                {'source': v, 'supported': supported}
            )
        return v

    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v, info):
        source = info.data.get('source')
        if source == 'github' and ':' not in v:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'invalid_github_identifier',
                'GitHub identifier must be in format owner:repo'
            )
        return v


class NormalizationRequest(BaseModel):
    """Request model for data normalization."""
    source: str
    data: dict
    correlation_id: Optional[str] = None

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        supported = ['github', 'jira', 'confluence']
        if v not in supported:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'source_not_supported',
                'Unsupported source: {source}. Must be one of {supported}',
                {'source': v, 'supported': supported}
            )
        return v


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'text_required',
                'Text field is required and cannot be empty'
            )
        return v
