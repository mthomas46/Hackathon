"""Validation logic for secure analyzer service."""


def validate_content(content: str) -> str:
    """Validate content field."""
    if not content:
        raise ValueError('Content cannot be empty')
    if len(content) > 1000000:  # 1MB limit
        raise ValueError('Content too large (max 1MB)')
    return content


def validate_keywords(keywords: list) -> list:
    """Validate keywords field."""
    if keywords is not None:
        if len(keywords) > 1000:
            raise ValueError('Too many keywords (max 1000)')
        for keyword in keywords:
            if len(keyword) > 500:
                raise ValueError('Keyword too long (max 500 characters)')
    return keywords


def validate_providers(providers: list) -> list:
    """Validate providers field."""
    if providers is not None:
        for provider in providers:
            if not isinstance(provider, dict):
                raise ValueError('Each provider must be a dictionary')
            if 'name' not in provider:
                raise ValueError('Each provider must have a name field')
            if len(provider.get('name', '')) > 100:
                raise ValueError('Provider name too long (max 100 characters)')
    return providers
