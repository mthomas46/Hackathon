"""Document ID value object for DDD compliance."""

import re
from typing import Optional


class DocumentId:
    """Value object for document ID with validation."""

    def __init__(self, value: str):
        if not value or not isinstance(value, str):
            raise ValueError("Document ID must be a non-empty string")

        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError("Document ID must contain only alphanumeric characters, underscores, and hyphens")

        if len(value) > 100:
            raise ValueError("Document ID must be 100 characters or less")

        self._value = value

    @property
    def value(self) -> str:
        """Get the document ID value."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DocumentId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
