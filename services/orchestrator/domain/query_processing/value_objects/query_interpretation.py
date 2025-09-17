"""Query Interpretation Value Object"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .query_intent import QueryIntent
from .query_confidence import QueryConfidence
from .query_type import QueryType


class QueryInterpretation:
    """Value object representing the interpretation of a natural language query."""

    def __init__(
        self,
        query_id: str,
        intent: QueryIntent,
        confidence: QueryConfidence,
        confidence_score: float,
        query_type: QueryType = QueryType.NATURAL_LANGUAGE,
        entities: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        suggested_actions: Optional[List[str]] = None,
        clarification_questions: Optional[List[str]] = None,
        alternative_interpretations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        interpretation_timestamp: Optional[datetime] = None
    ):
        self._query_id = query_id
        self._intent = intent
        self._confidence = confidence
        self._confidence_score = max(0.0, min(1.0, confidence_score))
        self._query_type = query_type
        self._entities = entities or {}
        self._parameters = parameters or {}
        self._suggested_actions = suggested_actions or []
        self._clarification_questions = clarification_questions or []
        self._alternative_interpretations = alternative_interpretations or []
        self._metadata = metadata or {}
        self._interpretation_timestamp = interpretation_timestamp or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate query interpretation data."""
        if not self._query_id:
            raise ValueError("Query ID cannot be empty")

        if self._confidence_score < 0.0 or self._confidence_score > 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

    @property
    def query_id(self) -> str:
        """Get the query ID."""
        return self._query_id

    @property
    def intent(self) -> QueryIntent:
        """Get the recognized intent."""
        return self._intent

    @property
    def confidence(self) -> QueryConfidence:
        """Get the confidence level."""
        return self._confidence

    @property
    def confidence_score(self) -> float:
        """Get the numeric confidence score (0.0 to 1.0)."""
        return self._confidence_score

    @property
    def query_type(self) -> QueryType:
        """Get the query type."""
        return self._query_type

    @property
    def entities(self) -> Dict[str, Any]:
        """Get extracted entities."""
        return self._entities.copy()

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get interpretation parameters."""
        return self._parameters.copy()

    @property
    def suggested_actions(self) -> List[str]:
        """Get suggested actions."""
        return self._suggested_actions.copy()

    @property
    def clarification_questions(self) -> List[str]:
        """Get clarification questions."""
        return self._clarification_questions.copy()

    @property
    def alternative_interpretations(self) -> List[Dict[str, Any]]:
        """Get alternative interpretations."""
        return self._alternative_interpretations.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get interpretation metadata."""
        return self._metadata.copy()

    @property
    def interpretation_timestamp(self) -> datetime:
        """Get the interpretation timestamp."""
        return self._interpretation_timestamp

    @property
    def can_execute(self) -> bool:
        """Check if interpretation can be executed."""
        return (
            self._intent.requires_execution and
            self._confidence.can_auto_execute and
            len(self._parameters) > 0
        )

    @property
    def needs_clarification(self) -> bool:
        """Check if interpretation needs clarification."""
        return (
            self._confidence.requires_clarification or
            len(self._clarification_questions) > 0
        )

    @property
    def has_alternatives(self) -> bool:
        """Check if alternative interpretations are available."""
        return len(self._alternative_interpretations) > 0

    def add_entity(self, entity_type: str, entity_value: Any):
        """Add an extracted entity."""
        self._entities[entity_type] = entity_value

    def add_parameter(self, key: str, value: Any):
        """Add an interpretation parameter."""
        self._parameters[key] = value

    def add_suggested_action(self, action: str):
        """Add a suggested action."""
        self._suggested_actions.append(action)

    def add_clarification_question(self, question: str):
        """Add a clarification question."""
        self._clarification_questions.append(question)

    def add_alternative_interpretation(self, interpretation: Dict[str, Any]):
        """Add an alternative interpretation."""
        self._alternative_interpretations.append(interpretation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_id": self._query_id,
            "intent": self._intent.value,
            "confidence": self._confidence.value,
            "confidence_score": self._confidence_score,
            "query_type": self._query_type.value,
            "entities": self._entities,
            "parameters": self._parameters,
            "suggested_actions": self._suggested_actions,
            "clarification_questions": self._clarification_questions,
            "alternative_interpretations": self._alternative_interpretations,
            "metadata": self._metadata,
            "interpretation_timestamp": self._interpretation_timestamp.isoformat(),
            "can_execute": self.can_execute,
            "needs_clarification": self.needs_clarification,
            "has_alternatives": self.has_alternatives
        }

    def __repr__(self) -> str:
        return f"QueryInterpretation(query_id='{self._query_id}', intent={self._intent}, confidence={self._confidence}, score={self._confidence_score:.2f})"
