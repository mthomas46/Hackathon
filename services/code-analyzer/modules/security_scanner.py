"""Security scanning logic for code analyzer service."""

import re
from typing import List


# Security patterns for detecting sensitive information
SECURITY_PATTERNS = [
    r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9\-_/+=]{8,}['\"]",
    r"secret\s*[:=]",
    r"(password|passwd)\s*[:=]",
    r"Bearer\s+[A-Za-z0-9\-_.]+",
    r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
    r"-----BEGIN (?:RSA|EC|DSA) PRIVATE KEY-----",
    r"\bssn\b|social security",
    r"credit card|\b(?:\d{4}[- ]){3}\d{4}\b",
]


def scan_for_sensitive_content(content: str, additional_keywords: List[str] = None) -> dict:
    """Scan content for sensitive information and return findings.

    Args:
        content: Text content to scan
        additional_keywords: Optional list of additional keywords to flag

    Returns:
        Dict with 'sensitive' boolean and 'matches' list
    """
    patterns = SECURITY_PATTERNS.copy()

    # Add custom keywords if provided
    if additional_keywords:
        for keyword in additional_keywords:
            try:
                patterns.append(re.escape(keyword))
            except re.error:
                # Skip invalid regex patterns
                continue

    matches: List[str] = []

    # Scan for each pattern
    for pattern in patterns:
        for match in re.findall(pattern, content, flags=re.IGNORECASE):
            if match not in matches:
                matches.append(match)

    return {
        "sensitive": bool(matches),
        "matches": matches[:100]  # Limit results
    }
