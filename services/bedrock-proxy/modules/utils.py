"""Utility functions for bedrock proxy service."""

import re


def sanitize_for_response(text: str) -> str:
    """Sanitize text to prevent XSS attacks in JSON responses."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove dangerous JavaScript event handlers and attributes
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)

    # Remove quotes that could be used to break out of attributes
    text = text.replace('"', '').replace("'", '')

    # Remove SQL injection patterns
    text = re.sub(r';\s*--', '', text, flags=re.IGNORECASE)  # Remove SQL comments
    text = re.sub(r';\s*SELECT\s+.*?\s+FROM', '; SELECT * FROM dummy', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove environment variable patterns
    text = re.sub(r'\$\{[^}]+\}', '', text)

    # Remove path traversal patterns
    text = re.sub(r'\.\./', '', text)
    text = re.sub(r'\\', '', text)  # Remove backslashes
    text = re.sub(r'/', '', text)  # Remove forward slashes in path patterns

    # Remove null bytes and other control characters
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')

    return text.strip()


def bullets_from_text(text: str, max_items: int = 5) -> list[str]:
    """Extract bullet points from text content."""
    bullets: list[str] = []
    for line in (text or "").splitlines():
        s = line.strip(" -\t")
        if not s:
            continue
        if len(s) > 2:
            bullets.append(s)
        if len(bullets) >= max_items:
            break
    if not bullets:
        bullets = ["No content provided.", "Add more details to the prompt."]
    return bullets
