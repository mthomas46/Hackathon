"""Tag value object for DDD compliance."""

import re
from typing import Set


class Tag:
    """Value object for document tag with validation."""

    def __init__(self, value: str):
        if not value or not isinstance(value, str):
            raise ValueError("Tag must be a non-empty string")

        # Remove leading/trailing whitespace and convert to lowercase for consistency
        cleaned_value = value.strip().lower()

        if not cleaned_value:
            raise ValueError("Tag cannot be empty after trimming whitespace")

        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', cleaned_value):
            raise ValueError("Tag must contain only alphanumeric characters, spaces, hyphens, and underscores")

        if len(cleaned_value) > 50:
            raise ValueError("Tag must be 50 characters or less")

        self._value = cleaned_value

    @property
    def value(self) -> str:
        """Get the tag value."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)


class TagCollection:
    """Collection of tags with business rules."""

    def __init__(self, tags: Set[Tag] = None):
        self._tags = tags or set()

    def add(self, tag: Tag) -> None:
        """Add a tag to the collection."""
        if len(self._tags) >= 10:
            raise ValueError("Cannot have more than 10 tags")
        self._tags.add(tag)

    def remove(self, tag: Tag) -> None:
        """Remove a tag from the collection."""
        self._tags.discard(tag)

    def has_tag(self, tag: Tag) -> bool:
        """Check if collection contains a tag."""
        return tag in self._tags

    @property
    def tags(self) -> Set[Tag]:
        """Get all tags."""
        return self._tags.copy()

    @property
    def count(self) -> int:
        """Get number of tags."""
        return len(self._tags)
