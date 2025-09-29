"""Summarization Request Value Object"""

from typing import List, Optional, Dict, Any


class SummarizationRequest:
    """Value object representing a text summarization request."""

    def __init__(
        self,
        content: str,
        keywords: Optional[List[str]] = None,
        keyword_document: Optional[str] = None,
        override_policy: bool = False,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        style: str = "neutral"
    ):
        self._content = content.strip()
        self._keywords = keywords or []
        self._keyword_document = keyword_document.strip() if keyword_document else None
        self._override_policy = override_policy
        self._max_length = max_length
        self._min_length = min_length
        self._style = style.strip().lower()

        self._validate()

    def _validate(self):
        """Validate summarization request data."""
        if not self._content:
            raise ValueError("Content cannot be empty")

        if len(self._content) < 10:
            raise ValueError("Content must be at least 10 characters long")

        if self._max_length is not None and self._max_length <= 0:
            raise ValueError("Max length must be positive")

        if self._min_length is not None and self._min_length <= 0:
            raise ValueError("Min length must be positive")

        if self._min_length is not None and self._max_length is not None:
            if self._min_length >= self._max_length:
                raise ValueError("Min length must be less than max length")

        valid_styles = ["neutral", "formal", "casual", "technical", "executive"]
        if self._style not in valid_styles:
            raise ValueError(f"Style must be one of: {', '.join(valid_styles)}")

    @property
    def content(self) -> str:
        """Get the content to summarize."""
        return self._content

    @property
    def keywords(self) -> List[str]:
        """Get the keywords list."""
        return self._keywords.copy()

    @property
    def keyword_document(self) -> Optional[str]:
        """Get the keyword document."""
        return self._keyword_document

    @property
    def override_policy(self) -> bool:
        """Check if policy should be overridden."""
        return self._override_policy

    @property
    def max_length(self) -> Optional[int]:
        """Get the maximum summary length."""
        return self._max_length

    @property
    def min_length(self) -> Optional[int]:
        """Get the minimum summary length."""
        return self._min_length

    @property
    def style(self) -> str:
        """Get the summarization style."""
        return self._style

    @property
    def content_length(self) -> int:
        """Get the content length."""
        return len(self._content)

    @property
    def has_keywords(self) -> bool:
        """Check if keywords are provided."""
        return len(self._keywords) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "content": self._content,
            "keywords": self._keywords,
            "override_policy": self._override_policy,
            "style": self._style,
            "content_length": self.content_length,
            "has_keywords": self.has_keywords
        }

        if self._keyword_document:
            result["keyword_document"] = self._keyword_document

        if self._max_length:
            result["max_length"] = self._max_length

        if self._min_length:
            result["min_length"] = self._min_length

        return result

    def __repr__(self) -> str:
        return f"SummarizationRequest(content_length={self.content_length}, style='{self._style}', override_policy={self._override_policy})"
