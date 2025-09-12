"""Content detection and analysis for secure analyzer service."""

import re
import os
from typing import List, Dict, Any, Optional


# Default security patterns
DEFAULT_PATTERNS = [
    r"\bssn\b|\bsocial.security\b|\b\d{3}-\d{2}-\d{4}\b",  # SSN patterns
    r"\bcredit.card\b|\bccn\b|\bpan\b|\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b",  # Credit card patterns
    r"\bsecret\b|\bconfidential\b|\bproprietary\b|\btoken\b|\bprivate[_-]?key\b",  # Secret patterns
    r"\bapi[\s_-]?key\b|\baccess[\s_-]?key\b|\bsecret[\s_-]?key\b|\bdatabase[\s_-]?password\b|\bjwt[\s_-]?secret\b|\baws[\s_-]?access[\s_-]?key\b|\buser[\s_-]?ssn\b",  # Key patterns (expanded)
    r"\bsk-\w{20,}\b",  # OpenAI API key pattern (sk- followed by 20+ characters)
    r"\bakia\w{10,}\b",  # AWS access key pattern (akia followed by 10+ characters)
    r"\bclient.name\b|\bclient.id\b|\buser.name\b|\buser.id\b",  # Client/User patterns
    r"\bpassword\b|\bpwd\b|\bpass\b|\bauth\b|\bcredential\b",  # Password/Auth patterns
    r".*\bpassword\b.*=.*",  # Variable assignments with password (word boundary)
    r".*\bsecret\b.*=.*",    # Variable assignments with secret (word boundary)
    r".*\bkey\b.*=.*",       # Variable assignments with key (word boundary)
    r".*\btoken\b.*=.*",     # Variable assignments with token
    r".*\bssn\b.*=.*",       # Variable assignments with ssn
]


class ContentDetector:
    """Detects sensitive content in text using pattern matching."""

    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in DEFAULT_PATTERNS]

    def detect_sensitive_content(
        self,
        content: str,
        additional_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Detect sensitive content and return analysis results."""

        # Load additional keywords
        all_keywords = additional_keywords or []
        # TODO: Load keywords from URL if keyword_document is provided

        # Compile all patterns
        patterns = self._compile_patterns(all_keywords)

        # Find matches
        matches = self._find_matches(content, patterns)

        # Analyze topics
        topics = self._analyze_topics(content, matches)

        # Determine sensitivity
        sensitive = self._determine_sensitivity(content, matches)

        return {
            "sensitive": sensitive,
            "matches": matches[:100],  # Limit matches
            "topics": topics
        }

    def _compile_patterns(self, keywords: List[str]) -> List[re.Pattern[str]]:
        """Compile regex patterns from keywords."""
        patterns = self._patterns.copy()

        for keyword in keywords:
            try:
                patterns.append(re.compile(re.escape(keyword), re.IGNORECASE))
            except re.error:
                continue  # Skip invalid patterns

        return patterns

    def _find_matches(self, content: str, patterns: List[re.Pattern[str]]) -> List[str]:
        """Find all pattern matches in content."""
        matches = []

        for pattern in patterns:
            try:
                found_matches = pattern.findall(content or "")
                for match in found_matches:
                    if match not in matches:
                        matches.append(match)
            except Exception:
                continue  # Skip problematic patterns

        return matches

    def _analyze_topics(self, content: str, matches: List[str]) -> List[str]:
        """Analyze content to determine security topics."""
        topics = []
        content_lower = (content or "").lower()

        # Topic keyword mappings
        topic_keywords = {
            "pii": ["ssn", "social security", "credit card", "personal", "identity"],
            "secrets": ["password", "secret", "key", "token", "credential"],
            "auth": ["api", "authentication", "login", "access"],
            "client": ["client", "user", "customer"],
            "credentials": ["password", "key", "token", "secret"],
            "proprietary": ["proprietary", "confidential", "internal", "private"]
        }

        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                # Check for keyword matches with flexible matching
                if (keyword in content_lower or
                    re.search(r'\b' + re.escape(keyword) + r'\b', content_lower) or
                    re.search(r'\b' + re.escape(keyword) + r's?\b', content_lower) or  # Handle plurals
                    any(keyword in word for word in content_lower.split())):  # Handle compound words

                    if topic not in topics:
                        topics.append(topic)

                    # Also add specific keywords as topics if they're security terms
                    if keyword not in topics and keyword in ["credit card", "ssn", "password", "secret", "token", "key"]:
                        topics.append(keyword)
                    break

        return topics

    def _determine_sensitivity(self, content: str, matches: List[str]) -> bool:
        """Determine if content is sensitive based on matches and context."""
        if not matches:
            return False

        # Check for technical/educational context that might make content acceptable
        technical_context_indicators = [
            "algorithm", "hashing", "encryption", "tutorial", "documentation",
            "example", "learn", "guide", "how to", "best practice"
        ]

        content_lower = (content or "").lower()
        has_technical_context = any(indicator in content_lower for indicator in technical_context_indicators)

        # If we have matches but also technical context, be more lenient
        if matches and has_technical_context and len(matches) <= 3:
            return False  # Allow if only a few matches and clear technical context

        return len(matches) > 0


# Global content detector instance
content_detector = ContentDetector()
