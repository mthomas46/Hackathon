"""Query Type Value Object"""

from enum import Enum


class QueryType(Enum):
    """Enumeration of supported query types."""

    NATURAL_LANGUAGE = "natural_language"    # Free-form natural language queries
    STRUCTURED = "structured"                # Structured query with specific parameters
    HYBRID = "hybrid"                       # Combination of natural language and structured elements
    COMMAND = "command"                     # Direct command execution
    CONVERSATIONAL = "conversational"       # Multi-turn conversational queries

    @property
    def requires_interpretation(self) -> bool:
        """Check if this query type requires NLP interpretation."""
        return self in (QueryType.NATURAL_LANGUAGE, QueryType.HYBRID, QueryType.CONVERSATIONAL)

    @property
    def can_be_executed(self) -> bool:
        """Check if this query type can be directly executed."""
        return self != QueryType.CONVERSATIONAL

    @property
    def supports_context(self) -> bool:
        """Check if this query type supports conversational context."""
        return self in (QueryType.CONVERSATIONAL, QueryType.HYBRID)

    def __str__(self) -> str:
        return self.value
