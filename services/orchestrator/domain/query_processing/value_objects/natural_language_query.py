"""Natural Language Query Value Object"""

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


class NaturalLanguageQuery:
    """Value object representing a natural language query."""

    def __init__(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        query_id: Optional[str] = None
    ):
        self._query_id = query_id or str(uuid4())
        self._query = query.strip()
        self._user_id = user_id.strip() if user_id else None
        self._session_id = session_id.strip() if session_id else None
        self._context = context or {}
        self._timestamp = timestamp or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate natural language query data."""
        if not self._query:
            raise ValueError("Query cannot be empty")

        if len(self._query) > 5000:
            raise ValueError("Query too long (max 5000 characters)")

        if len(self._query) < 3:
            raise ValueError("Query too short (min 3 characters)")

    @property
    def query_id(self) -> str:
        """Get the unique query ID."""
        return self._query_id

    @property
    def query(self) -> str:
        """Get the query text."""
        return self._query

    @property
    def user_id(self) -> Optional[str]:
        """Get the user ID."""
        return self._user_id

    @property
    def session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self._session_id

    @property
    def context(self) -> Dict[str, Any]:
        """Get the query context."""
        return self._context.copy()

    @property
    def timestamp(self) -> datetime:
        """Get the query timestamp."""
        return self._timestamp

    @property
    def query_length(self) -> int:
        """Get the query length."""
        return len(self._query)

    @property
    def word_count(self) -> int:
        """Get the word count."""
        return len(self._query.split())

    @property
    def has_context(self) -> bool:
        """Check if query has additional context."""
        return len(self._context) > 0

    @property
    def is_conversational(self) -> bool:
        """Check if this appears to be part of a conversation."""
        return self._session_id is not None or self.has_context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "query_id": self._query_id,
            "query": self._query,
            "timestamp": self._timestamp.isoformat(),
            "query_length": self.query_length,
            "word_count": self.word_count,
            "has_context": self.has_context,
            "is_conversational": self.is_conversational
        }

        if self._user_id:
            result["user_id"] = self._user_id

        if self._session_id:
            result["session_id"] = self._session_id

        if self._context:
            result["context"] = self._context

        return result

    def __repr__(self) -> str:
        return f"NaturalLanguageQuery(query_id='{self._query_id}', query='{self._query[:50]}...', user_id='{self._user_id}')"
