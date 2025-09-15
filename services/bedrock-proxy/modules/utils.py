"""Utility functions for bedrock proxy service.

Provides helper functions for text processing, sanitization, and content generation.
"""
import re


def sanitize_for_response(text: str) -> str:
    """Sanitize text to prevent XSS attacks and injection in JSON responses.

    Performs comprehensive sanitization including:
    - HTML tag removal
    - JavaScript injection prevention
    - SQL injection pattern removal
    - Path traversal prevention
    - Control character filtering

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text safe for JSON response inclusion
    """
    if not text:
        return ""

    # Remove HTML tags to prevent XSS
    text = re.sub(r'<[^>]+>', '', text)

    # Remove dangerous JavaScript patterns
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)

    # Remove quotes that could break out of string contexts
    text = text.replace('"', '').replace("'", '')

    # Remove SQL injection patterns
    text = re.sub(r';\s*--', '', text, flags=re.IGNORECASE)  # SQL comments
    text = re.sub(r';\s*SELECT\s+.*?\s+FROM', '; SELECT * FROM dummy', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove environment variable patterns
    text = re.sub(r'\$\{[^}]+\}', '', text)

    # Remove path traversal patterns
    text = re.sub(r'\.\./', '', text)
    text = re.sub(r'\\', '', text)  # Backslashes
    text = re.sub(r'/', '', text)  # Forward slashes in dangerous contexts

    # Remove null bytes and other control characters (keep basic whitespace)
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')

    return text.strip()


def bullets_from_text(text: str, max_items: int = 5) -> list[str]:
    """Extract meaningful bullet points from input text content.

    Parses text line by line, extracting non-empty lines as bullet points.
    Provides fallback content if no meaningful text is found.

    Args:
        text: Input text to extract bullet points from
        max_items: Maximum number of bullet points to extract

    Returns:
        List of bullet point strings, with fallback content if empty
    """
    bullets: list[str] = []

    for line in (text or "").splitlines():
        # Clean line by removing common bullet markers and whitespace
        cleaned_line = line.strip(" -\t")
        if not cleaned_line:
            continue

        # Only include lines with meaningful content (more than just punctuation)
        if len(cleaned_line) > 2:
            bullets.append(cleaned_line)

        # Stop when we reach the maximum number of items
        if len(bullets) >= max_items:
            break

    # Provide helpful fallback content if no bullets were extracted
    if not bullets:
        bullets = [
            "No content provided.",
            "Add more details to the prompt for better analysis."
        ]

    return bullets
